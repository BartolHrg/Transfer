#!/bin/bash

# Bash Network Transfer Scripts

# Usage functions
usage_recv() {
	echo "Receive Script Usage:"
	echo "./recv.sh <port> <type> [save_path_for_file]"
	echo "Types:"
	echo "  m - Receive message"
	echo "  f - Receive file"
	echo "Example:"
	echo "  ./recv.sh 12345 m"
	echo "  ./recv.sh 12345 f /path/to/save/directory"
	exit 1
}

# Receive Script
# Check arguments
if [[ $# -lt 2 ]]; then
	usage_recv
fi

PORT=$1
TYPE=$2
SAVE_PATH=${3:-.}  # Default to current directory if not specified

# Validate type
if [[ "$TYPE" != "m" && "$TYPE" != "f" ]]; then
	echo "Invalid type. Use 'm' for message or 'f' for file."
	usage_recv
fi

# Get local IP
LOCAL_IP=$(hostname -I | awk '{print $1}')
echo "Listening IP: $LOCAL_IP"

# Message mode
if [[ "$TYPE" == "m" ]]; then
	echo "Listening for messages on port $PORT. Press Ctrl+C to stop."
	nc -lu "$PORT"
fi

# File mode
if [[ "$TYPE" == "f" ]]; then
	# Ensure save path exists
	mkdir -p "$SAVE_PATH"

	echo "Listening for file transfers on port $PORT. Press Ctrl+C to stop."
	
	# Receive file using netcat
	nc -l "$PORT" | (
		# Read filename length (4 bytes)
		read -n 4 filename_length_str
		filename_length=$((10#$filename_length_str))

		# Read filename
		read -n "$filename_length" filename

		# Read file size (8 bytes)
		read -n 8 filesize_str
		filesize=$((10#$filesize_str))

		# Full file path
		filepath="$SAVE_PATH/$filename"

		# Receive file contents
		dd bs=4096 of="$filepath"

		# Verify file size
		received_size=$(stat -c%s "$filepath")
		if [[ "$received_size" -eq "$filesize" ]]; then
			echo "File received successfully: $filepath"
		else
			echo "File transfer incomplete. Expected $filesize bytes, got $received_size bytes."
			rm "$filepath"
		fi
	)
fi