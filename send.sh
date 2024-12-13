#!/bin/bash

# Bash Network Transfer Scripts

# Usage functions
usage_send() {
	echo "Send Script Usage:"
	echo "./send.sh <receiver_ip> <port> <type> <file_or_message_path>"
	echo "Types:"
	echo "  m - Send message"
	echo "  f - Send file"
	echo "Example:"
	echo "  ./send.sh 192.168.1.100 12345 m \"Hello World\""
	echo "  ./send.sh 192.168.1.100 12345 f /path/to/file.txt"
	exit 1
}

# Send Script
# Check arguments
if [[ $# -lt 4 ]]; then
	usage_send
fi

RECEIVER_IP=$1
PORT=$2
TYPE=$3
FILE_OR_MESSAGE=$4

# Validate type
if [[ "$TYPE" != "m" && "$TYPE" != "f" ]]; then
	echo "Invalid type. Use 'm' for message or 'f' for file."
	usage_send
fi

# Message mode
if [[ "$TYPE" == "m" ]]; then
	# Using netcat for UDP message sending
	echo -n "$FILE_OR_MESSAGE" | nc -u "$RECEIVER_IP" "$PORT"
	if [[ $? -eq 0 ]]; then
		echo "Message sent successfully."
	else
		echo "Error sending message."
		exit 1
	fi
fi

# File mode
if [[ "$TYPE" == "f" ]]; then
	# Check if file exists
	if [[ ! -f "$FILE_OR_MESSAGE" ]]; then
		echo "File not found: $FILE_OR_MESSAGE"
		exit 1
	fi

	# Get filename and file size
	FILENAME=$(basename "$FILE_OR_MESSAGE")
	FILESIZE=$(stat -c%s "$FILE_OR_MESSAGE")

	# Using netcat for TCP file transfer
	{
		# Send filename length (4 bytes)
		printf '%04d' ${#FILENAME}
		# Send filename
		echo -n "$FILENAME"
		# Send file size (8 bytes)
		printf '%08d' "$FILESIZE"
		# Send file contents
		cat "$FILE_OR_MESSAGE"
	} | nc -N "$RECEIVER_IP" "$PORT"

	if [[ $? -eq 0 ]]; then
		echo "File sent successfully: $FILENAME"
	else
		echo "Error sending file."
		exit 1
	fi
fi
