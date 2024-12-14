#!/usr/bin/env python3

import argparse
import socket
import os
import struct
import sys

def receive_message(port):
	"""Receive a UDP message"""
	try:
		with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
			# Bind to all interfaces
			sock.bind(('0.0.0.0', port))
			
			print(f"Listening for messages on port {port}. Press Ctrl+C to stop.")
			
			# Receive message
			data, addr = sock.recvfrom(1024)
			print(f"Message from {addr}: {data.decode()}")
		
	except Exception as e:
		print(f"Error receiving message: {e}")

def receive_file(port, save_path='.'):
	"""Receive a file via TCP"""
	try:
		# Ensure save path exists
		os.makedirs(save_path, exist_ok=True)
		
		# Create socket and listen
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
			sock.bind(('0.0.0.0', port))
			sock.listen(1)
			
			print(f"Listening for file transfers on port {port}. Press Ctrl+C to stop.")
			
			# Accept connection
			conn, addr = sock.accept()
			with conn:
				print(f"Connection from {addr}")
				
				# Read filename length (4 bytes)
				filename_length_bytes = conn.recv(4)
				filename_length = struct.unpack('!I', filename_length_bytes)[0]
				
				# Read filename
				filename_bytes = conn.recv(filename_length)
				filename = filename_bytes.decode('utf-8')
				
				# Read file size (8 bytes)
				filesize_bytes = conn.recv(8)
				filesize = struct.unpack('!Q', filesize_bytes)[0]
				
				# Full file path
				filepath = os.path.join(save_path, filename)
				
				# Receive file contents
				with open(filepath, 'wb') as file:
					bytes_received = 0
					while bytes_received < filesize:
						# Read in chunks
						chunk = conn.recv(min(4096, filesize - bytes_received))
						if not chunk:
							break
						file.write(chunk)
						bytes_received += len(chunk)
						
						# Optional: Progress tracking
						progress = (bytes_received / filesize) * 100
						print(f"\rReceiving {filename}: {progress:.2f}%", end='', flush=True)
				
				print(f"\nFile received successfully: {filepath}")
		
	except Exception as e:
		print(f"Error receiving file: {e}")

parser = argparse.ArgumentParser(description="Network File/Message Transfer Utility")
	
# Receive mode
parser.add_argument('port', type=int, help='Port number')
parser.add_argument('type', choices=['m', 'f'], help='Transfer type: m (message) or f (file)')
parser.add_argument('save_path', nargs='?', default='.', 
						help='Save path for files (optional, default: current directory)')

args = parser.parse_args()

if args.type == 'm':
	receive_message(args.port)
else:
	receive_file(args.port, args.save_path)
