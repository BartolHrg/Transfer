#!/usr/bin/env python3

import argparse;
import socket;
import os;
import sys;
import json;
import re;

import tkinter as tk;
from tkinter import ttk, filedialog;
import traceback;

from typing import TypedDict;

# my_ip [port] -> [dst_ip] [dst_port]
# 
# Send               | Recv                 
#                    |                      
# [msg]     [->]     | [msg]       [<-]     
# [file][br][->]     | [folder][br][<-]     
#                    |                      

class Config(TypedDict):
	port: int;
	dst_ip: str;
	dst_port: str;
	last_file: str;
	last_dst: str;
	size_limit: float;
pass

CNOFIG_PATH = "./config.json";
if not os.path.exists(CNOFIG_PATH): 
	with open(CNOFIG_PATH, "w") as file:
		config: Config = {
			"port"      : 8840,
			"dst_ip"    : "",
			"dst_port"  : 8840,
			"last_file" : "",
			"last_dst"  : "D:/temp/",
			"size_limit": 2
		};
		json.dump(config, file);
	pass
else:
	with open(CNOFIG_PATH) as file: 
		config: Config = json.load(file);
	pass
pass
config: Config;
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
	s.connect(("1.2.3.4", 80));
	my_ip = s.getsockname()[0];
pass

def log(variable: tk.Variable, msg: str):
	variable.set(msg);
	output_frame.update();  output_frame.update_idletasks();
pass

def sizeToStr(x: int):
	(x, b) = divmod(x, 1024);
	(x, kb) = divmod(x, 1024);
	(x, mb) = divmod(x, 1024);
	(x, gb) = divmod(x, 1024);
	r = "";
	if gb: r += f"{gb} GB ";
	if mb: r += f"{mb} MB ";
	if kb: r += f"{kb} kB ";
	if b: r += f"{b} B ";
	if not r: r = "0";
	return r.strip();
pass

def sendMessage():
	"""Send a UDP message"""
	log(log_var, "Sending message");
	try:
		receiver_ip = dst_ip_var.get();
		port = dst_port_var.get();
		message = send_msg_var.get();
		with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
			sock.sendto(message.encode("utf-8"), (receiver_ip, port));
		pass
		log(log_var, "Message sent");
	except:
		log(log_var, traceback.format_exc());
	pass
pass
def sendFile():
	"""Send a file via TCP"""
	log(log_var, "");
	try:
		log(filename_var, "Sending:  ?: ");
		log(progress_var, "");
		receiver_ip = dst_ip_var.get();
		port = dst_port_var.get();
		filepath = send_file_var.get();
		log(filename_var, f"Sending:  {filepath}: ");
		log(progress_var, "0 %");
		if not os.path.isfile(filepath): raise FileNotFoundError(f"File not found: {filepath}")

		with open(filepath, "rb") as file, socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
			sock.connect((receiver_ip, port));
			filename = os.path.basename(filepath);
			filesize = os.path.getsize(filepath);
			filename_bytes = filename.encode("utf-8");
			
			# Send filename length (4 bytes) and filename
			sock.send(len(filename_bytes).to_bytes(4, "little", signed = False));
			sock.send(filename_bytes);
			
			# Send file size (8 bytes) and contents
			sock.send(filesize.to_bytes(8, "little", signed = False));
			total_sent = 0;
			while True:
				chunk = file.read(4096);
				if not chunk: break;
				sock.sendall(chunk);
				total_sent += len(chunk);
				
				# Optional: Progress tracking
				progress = (total_sent / filesize) * 100;
				log(progress_var, f"{progress:.2f} %");
			pass
			log(progress_var, "Done");
		pass
	except:
		log(log_var, traceback.format_exc());
	pass
pass
def receiveMessage():
	"""Receive a UDP message"""
	log(log_var, "Receiving message");
	try:
		port = my_port_var.get();
		with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
			# Bind to all interfaces
			sock.bind(("0.0.0.0", port));
			log(log_var, f"Receiving message on port {port}");
			
			(data, addr) = sock.recvfrom(1024);
			msg = data.decode("utf-8");
			recv_msg_var.set(msg);
			log(log_var, "Message received");
		pass
	except:
		log(log_var, traceback.format_exc());
	pass
pass
def receiveFile():
	"""Receive a file via TCP"""
	log(log_var, "");
	try:
		log(filename_var, "Receiving:  ?: ");
		log(progress_var, "");
		port = my_port_var.get();
		save_path = recv_path_var.get();
		os.makedirs(save_path, exist_ok=True);
		
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
			sock.bind(("0.0.0.0", port));
			sock.listen(1);
			log(log_var, f"Listening for file transfers on port {port}.");
			
			(conn, addr) = sock.accept();
			with conn:
				log(log_var, 
					f"Listening for file transfers on port {port}." "\n"
					f"Connection from {addr}"
				);
				
				# Read filename length (4 bytes) and filename
				filename_length = int.from_bytes(conn.recv(4), "little", signed = False);
				filename_bytes = conn.recv(filename_length);
				filename = filename_bytes.decode("utf-8");
				log(filename_var, f"Receiving:  {filename} []: ");
				log(progress_var, "0 %");
				filepath = save_path + "/" + filename;
				
				# Read file size (8 bytes) and contents
				filesize = int.from_bytes(conn.recv(8), "little", signed = False);
				log(filename_var, f"Receiving:  {filename} [{sizeToStr(filesize)}]: ");
				if filesize > round(size_limit_var.get() * 1024**3): 
					raise ValueError(f"File size too large: {sizeToStr(filesize)}");
				pass
				with open(filepath, "wb") as file:
					bytes_received = 0;
					while bytes_received < filesize:
						chunk = conn.recv(min(4096, filesize - bytes_received))
						if not chunk: break;
						file.write(chunk);
						bytes_received += len(chunk);
						
						# Optional: Progress tracking
						progress = (bytes_received / filesize) * 100;
						log(progress_var, f"{progress:.2f} %");
					pass
				pass
				log(progress_var, "Done");
			pass
		pass
	except:
		log(log_var, traceback.format_exc());
	pass
pass

class NumberVar(tk.StringVar):
	def get(self) -> int | float:
		raw = super().get();
		raw = re.sub(r"\s", "", raw);
		if not raw: return 0;
		if "." not in raw: return int(raw);
		x = float(raw);
		if x.is_integer(): return int(x);
		return x;
	pass
pass


window = tk.Tk();
window.geometry("800x500");

frame = ttk.Frame(window);
frame.pack(expand = True, fill = tk.BOTH, padx = 20, pady = 20);

ip_frame     = ttk.Frame     (frame);
sr_frame     = ttk.Frame(frame);
send_frame   = ttk.LabelFrame(sr_frame, text = "Send");
recv_frame   = ttk.LabelFrame(sr_frame, text = "Receive");
output_frame = ttk.LabelFrame(frame, text = "Output");

ip_frame    .pack(side = tk.TOP   , fill = tk.X,                anchor = tk.NW);
sr_frame    .pack(side = tk.TOP   , fill = tk.X, expand = True, anchor = tk.N);
send_frame  .pack(side = tk.LEFT  , fill = tk.X, expand = True, anchor = tk.N);
recv_frame  .pack(side = tk.RIGHT , fill = tk.X, expand = True, anchor = tk.N);
output_frame.pack(side = tk.TOP   , fill = tk.X,                anchor = tk.NW);

my_port_var  = tk.IntVar   (ip_frame, config["port"]);
dst_ip_var   = tk.StringVar(ip_frame, config["dst_ip"]);
dst_port_var = tk.IntVar   (ip_frame, config["dst_port"]);
ttk.Label  (ip_frame, text = my_ip                 ).pack(side = tk.LEFT, padx = 10);
ttk.Spinbox(ip_frame, textvariable = my_port_var   ).pack(side = tk.LEFT, padx = 10);
ttk.Label  (ip_frame, text = "🡠🡢"                  ).pack(side = tk.LEFT, padx = 10);
ttk.Entry  (ip_frame, textvariable = dst_ip_var    ).pack(side = tk.LEFT, padx = 10);
ttk.Spinbox(ip_frame, textvariable = dst_port_var  ).pack(side = tk.LEFT, padx = 10);

send_msg_var   = tk.StringVar(send_frame);
send_file_var  = tk.StringVar(send_frame, config["last_file"]);
recv_msg_var   = tk.StringVar(recv_frame);
recv_path_var  = tk.StringVar(recv_frame, config["last_dst"]);
size_limit_var =    NumberVar(recv_frame, config["size_limit"]);
filename_var   = tk.StringVar(frame);
progress_var   = tk.StringVar(frame);
log_var        = tk.StringVar(frame);

send_frame.columnconfigure(1, weight = 1);
recv_frame.columnconfigure(1, weight = 1);

def chooseSendFile():
	path = filedialog.askopenfilename(initialfile = send_file_var.get());
	if not path: return;
	send_file_var.set(path);
	log(send_file_var, path);
	output_frame.update(); output_frame.update_idletasks();
pass
ttk.Entry(send_frame, textvariable = send_msg_var               ).grid(row = 1, column = 1, columnspan = 2, sticky = tk.NSEW);
ttk.Entry(send_frame, textvariable = send_file_var              ).grid(row = 2, column = 1, sticky = tk.NSEW);
ttk.Button(send_frame, text = "Browse", command = chooseSendFile).grid(row = 2, column = 2, sticky = tk.NSEW);
tk.Button(send_frame, text = "🡢", background = "cyan", command = sendMessage).grid(row = 1, column = 3);
tk.Button(send_frame, text = "🡢", background = "cyan", command = sendFile   ).grid(row = 2, column = 3);

def chooseRecvPath():
	path = filedialog.askdirectory(initialdir = recv_path_var.get());
	if not path: return;
	recv_path_var.set(path);
	log(recv_path_var, path);
	output_frame.update(); output_frame.update_idletasks();
pass
ttk.Entry(recv_frame, textvariable = recv_msg_var               ).grid(row = 1, column = 1, columnspan = 2, sticky = tk.NSEW);
ttk.Entry(recv_frame, textvariable = recv_path_var              ).grid(row = 2, column = 1, sticky = tk.NSEW);
ttk.Button(recv_frame, text = "Browse", command = chooseRecvPath).grid(row = 2, column = 2, sticky = tk.NSEW);
tk.Button(recv_frame, text = "🡠", background = "cyan", command = receiveMessage).grid(row = 1, column = 3);
tk.Button(recv_frame, text = "🡠", background = "cyan", command = receiveFile   ).grid(row = 2, column = 3);
size_limit_frame = ttk.Frame(recv_frame);
size_limit_frame.grid(row = 3, column = 1, columnspan = 3, sticky = tk.NSEW);
ttk.Label(size_limit_frame, text = "Max: ").pack(side = tk.LEFT);
ttk.Spinbox(size_limit_frame, textvariable = size_limit_var).pack(side = tk.LEFT, fill = tk.X);
ttk.Label(size_limit_frame, text = "GB").pack(side = tk.LEFT);

#	ttk.Label(output_frame, text = "Status: "          ).pack(side = tk.LEFT);
ttk.Label(output_frame, textvariable = log_var     ).pack(side = tk.BOTTOM, expand = True, fill = tk.BOTH);
ttk.Label(output_frame, textvariable = filename_var).pack(side = tk.LEFT);
ttk.Label(output_frame, textvariable = progress_var).pack(side = tk.LEFT);


def updateConfig(*_):
	config = {
		"port"      : my_port_var   .get(),
		"dst_ip"    : dst_ip_var    .get(),
		"dst_port"  : dst_port_var  .get(),
		"last_file" : send_file_var .get(),
		"last_dst"  : recv_path_var .get(),
		"size_limit": size_limit_var.get(),
	};
	with open(CNOFIG_PATH, "w") as file: json.dump(config, file);
pass
my_port_var   .trace("w", updateConfig);
dst_ip_var    .trace("w", updateConfig);
dst_port_var  .trace("w", updateConfig);
send_file_var .trace("w", updateConfig);
recv_path_var .trace("w", updateConfig);
size_limit_var.trace("w", updateConfig);

if "idlelib.run" not in sys.modules:
	window.mainloop();
pass
