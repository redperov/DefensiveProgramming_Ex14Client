import socket
import struct
from random import randint

# The maximum value a user ID can have
USER_ID_MAX_VALUE = (2 ** 32) - 1

# Client's version
VERSION = 1

# Server info file path
SERVER_INFO_PATH = "server.info"

# Backup files file path
BACKUP_FILES_PATH = "backup.info"

# Max packet size
MAX_PACKET_SIZE = 11 # TODO change to 1024

# Operations
BACKUP_FILE_OP = 100
RETRIEVE_FILE_OP = 200
DELETE_FILE_OP = 201
LIST_ALL_FILES_OP = 202

# Success responses
FILE_MODIFIED = 212  # includes file saving and deletion
FILE_RETRIEVED = 210
ALL_FILES_RETRIEVED = 211

# Failure responses
FILE_NOT_FOUND = 1001
USER_HAS_NO_FILES = 1002
GENERAL_ERROR = 1003


class Client:
    def __init__(self, server_host, server_port):
        # Get the server's host and port
        self.server_host, self.server_port = self.read_server_info()

        # Get the backup files
        self.backup_files = self.read_backup_files()

        # Client version
        self.version = VERSION

        # Generate a random id for the user
        self.user_id = randint(0, USER_ID_MAX_VALUE)
        print(f"User id: {self.user_id}")

    def start(self):
        try:
            self.get_backed_up_files()

            first_file_to_backup = self.backup_files[0]
            self.back_up_file(first_file_to_backup)

            second_file_to_backup = self.backup_files[1]
            self.back_up_file(second_file_to_backup)

            self.get_backed_up_files()

            self.get_backed_up_file(first_file_to_backup, "tmp")

            # TODO save only the payload
            # self.save_local_file(payload, "tmp")

            self.delete_backed_up_file(first_file_to_backup)

            self.get_backed_up_file(first_file_to_backup, "tmp")
        except Exception as e:
            print("Error occurred:", e)

        # version = 1
        # op = 100
        # filename = "myfile.txt"
        # payload = "hello"
        # name_len = len(filename)
        # size = len(payload)
        #
        # with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        #     s.connect((self.server_host, self.server_port))
        #     data = struct.pack(f"<IBBH{len(filename)}sI{len(payload)}s", self.user_id, version, op, name_len,
        #                        filename.encode('utf-8'), size, payload.encode('utf-8'))
        #     s.sendall(data)
        #     print("Message sent")
        #     data = s.recv(10)
        # print('Received', repr(data))

    def get_backed_up_files(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self.server_host, self.server_port))

            print("Retrieving backed up files")
            request = struct.pack("<IBB", self.user_id, self.version, LIST_ALL_FILES_OP)
            sock.sendall(request)

            # Read response header
            server_version = struct.unpack("<B", sock.recv(1))
            status = struct.unpack("<H", sock.recv(2))[0]

            if status == ALL_FILES_RETRIEVED:
                filename, payload = self.read_response_list_all_files(sock)
                print(f"Server response:\nFilename: {filename}\nPayload:\n{payload}")
                return filename, payload
            elif status == USER_HAS_NO_FILES:
                print("No files backed up in the server")
                return None
            elif status == GENERAL_ERROR:
                print("An error occurred in the server")
                return None
            else:
                raise ValueError(f"Illegal response status: {status}")

    def get_backed_up_file(self, filename, output_file):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self.server_host, self.server_port))

            print(f"Retrieving file: {filename} from server")
            name_len = len(filename)
            request = struct.pack(f"<IBBH{name_len}s", self.user_id, self.version, RETRIEVE_FILE_OP, name_len,
                                  filename.encode('utf-8'))
            sock.sendall(request)

            # Read response header
            server_version = struct.unpack("<B", sock.recv(1))
            status = struct.unpack("<H", sock.recv(2))[0]

            if status == FILE_RETRIEVED:
                filename = self.read_response_with_retrieved_file(sock, output_file)
                print(f"Server response:\nFilename: {filename}\nPayload saved to: {output_file}")
                return filename
            elif status == FILE_NOT_FOUND:
                print("File not found: " + self.read_response_with_filename(sock))
                return None
            elif status == GENERAL_ERROR:
                print("An error occurred in the server")
                return None
            else:
                raise ValueError(f"Illegal response status: {status}")

    def back_up_file(self, filename):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self.server_host, self.server_port))
            print(f"Backing up file: {filename}")

            # TODO send in chunks
            with open(filename) as file:
                payload = file.read()

            # Send the request
            name_len = len(filename)
            size = len(payload)
            request = struct.pack(f"<IBBH{name_len}sI{size}s", self.user_id, self.version, BACKUP_FILE_OP, name_len,
                                  filename.encode('utf-8'), size, payload.encode('utf-8'))
            sock.sendall(request)

            # Read response header
            server_version = struct.unpack("<B", sock.recv(1))
            status = struct.unpack("<H", sock.recv(2))[0]

            if status == FILE_MODIFIED:
                print("File saved: " + self.read_response_with_filename(sock))
            elif status == GENERAL_ERROR:
                print("An error occurred in the server")
            else:
                raise ValueError(f"Illegal response status: {status}")

    def delete_backed_up_file(self, filename):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self.server_host, self.server_port))

            print(f"Deleting backed up file: {filename} from server")
            name_len = len(filename)
            request = struct.pack(f"<IBBH{name_len}s", self.user_id, self.version, DELETE_FILE_OP, name_len,
                                  filename.encode('utf-8'))
            sock.sendall(request)

            # Read response header
            server_version = struct.unpack("<B", sock.recv(1))
            status = struct.unpack("<H", sock.recv(2))[0]

            if status == FILE_MODIFIED:
                print("File deleted: " + self.read_response_with_filename(sock))
            elif status == FILE_NOT_FOUND:
                print("File not found: " + self.read_response_with_filename(sock))
            elif status == GENERAL_ERROR:
                return print("An error occurred in the server")
            else:
                raise ValueError(f"Illegal response status: {status}")

    @staticmethod
    def read_server_info():
        """
        Reads the host and port from the server info file.

        :return: host, port
        """
        with open(SERVER_INFO_PATH) as file:
            data = file.readline().split(":")
            host = data[0]
            port = int(data[1])
            return host, port

    @staticmethod
    def read_backup_files():
        """
        Reads the client's backup files names.

        :return: list of names of backup files
        """
        file_names = []
        with open(BACKUP_FILES_PATH) as file:
            lines = file.readlines()

        for filename in lines:
            file_names.append(filename.strip())

        return file_names

    @staticmethod
    def read_response_with_filename(sock):

        # Read the filename
        name_len = struct.unpack("<H", sock.recv(2))[0]
        filename = struct.unpack(f"<{name_len}s", sock.recv(name_len))[0].decode('utf-8')

        return filename

    @staticmethod
    def read_response_with_retrieved_file(sock, output_file):
        # Read the filename
        name_len = struct.unpack("<H", sock.recv(2))[0]
        filename = struct.unpack(f"<{name_len}s", sock.recv(name_len))[0].decode('utf-8')

        # Read the payload
        size = struct.unpack("<I", sock.recv(4))[0]
        data_counter = 0

        with open(output_file, "w") as file:
            while True:
                data = sock.recv(MAX_PACKET_SIZE)
                data_counter += len(data)
                if not data or data_counter > size:
                    break
                file.write(data.decode("utf-8"))

        # payload = ""
        # curr_offset = 0

        # while True:
        #     if (size - curr_offset) <= 0:
        #         break
        #     next_packet_size = min(size - curr_offset, MAX_PACKET_SIZE)
        #     response = struct.unpack(f"<{next_packet_size}s", sock.recv(size))[0].decode('utf-8')
        #     payload += response
        #     curr_offset += next_packet_size

        # TODO read in chunks (should probably print straight away)
        # payload = struct.unpack(f"<{size}s", sock.recv(size))[0].decode('utf-8')

        return filename

    @staticmethod
    def read_response_list_all_files(sock):
        # Read the filename
        name_len = struct.unpack("<H", sock.recv(2))[0]
        filename = struct.unpack(f"<{name_len}s", sock.recv(name_len))[0].decode('utf-8')

        # Read the payload
        size = struct.unpack("<I", sock.recv(4))[0]
        payload = struct.unpack(f"<{size}s", sock.recv(size))[0].decode('utf-8')

        return filename, payload

    # @staticmethod
    # def save_local_file(payload, destination_path):
    #     with open(destination_path, "w") as file:
    #         file.write(payload)

