#!/usr/bin/env python3

import argparse
import socket
import os
import struct
import sys

def send_message(receiver_ip, port, message):
	"""Send a UDP message"""
	with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
		sock.sendto(message.encode(), (receiver_ip, port))
	print(f"Message sent successfully to {receiver_ip}:{port}")


def send_file(receiver_ip, port, filepath):
	"""Send a file via TCP"""
	# Validate file exists
	if not os.path.isfile(filepath):
		raise FileNotFoundError(f"File not found: {filepath}")

	# Open file and socket
	with open(filepath, 'rb') as file, socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
		
		# Connect to receiver
		sock.connect((receiver_ip, port))
		
		# Get filename and file size
		filename = os.path.basename(filepath)
		filesize = os.path.getsize(filepath)
		
		# Prepare filename (as UTF-8 bytes)
		filename_bytes = filename.encode('utf-8')
		
		# Send filename length (4 bytes)
		sock.send(len(filename_bytes).to_bytes(4, "little", signed = False));
		
		# Send filename
		sock.send(filename_bytes)
		
		# Send file size (8 bytes)
		sock.send(filesize.to_bytes(8, "little", signed = False));
		
		# Send file contents
		total_sent = 0
		while True:
			chunk = file.read(4096)
			if not chunk:
				break
			sock.sendall(chunk)
			total_sent += len(chunk)
			
			# Optional: Progress tracking
			progress = (total_sent / filesize) * 100
			print(f"\rSending {filename}: {progress:.2f}%", end='', flush=True)
		
		print(f"\nFile sent successfully: {filename}")

parser = argparse.ArgumentParser(description="Network File/Message Transfer Utility")
	
# Send mode
parser.add_argument('receiver_ip', help='Receiver IP address')
parser.add_argument('port', type=int, help='Port number')
parser.add_argument('type', choices=['m', 'f'], help='Transfer type: m (message) or f (file)')
parser.add_argument('content', help='Message or file path')

args = parser.parse_args()

if args.type == 'm':
	send_message(args.receiver_ip, args.port, args.content)
else:
	send_file(args.receiver_ip, args.port, args.content)

