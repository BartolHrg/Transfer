# Receiver Script (save as Receive-Message.ps1)


param(
	[Parameter(Mandatory=$true)]
	[int]$Port,

	[Parameter(Mandatory=$true)]
	[ValidateSet('f', 'm')]
	[string]$typ,

	[Parameter(Mandatory={$typ -eq 'f'})]
	[string]$SavePath
)



if ($typ -eq "m") {
	try {
		$endpoint = New-Object System.Net.IPEndPoint([IPAddress]::Any, $Port)
		$udpclient = New-Object System.Net.Sockets.UdpClient($Port)
		
		$localip = (Get-NetIPAddress | Where-Object { $_.AddressFamily -eq "IPv4" -and $_.PrefixOrigin -eq "Dhcp" }).IPAddress
		Write-Host "ip = $localip"
	
		Write-Host "Listening for messages on port $Port. Press Ctrl+C to stop."

		$content = $udpclient.Receive([ref]$endpoint)
		$message = [Text.Encoding]::ASCII.GetString($content)
		Write-Host "Message received from $($endpoint.Address): $message"
	}
	catch {
		Write-Host "Error receiving message: $_"
	}
	finally {
		if ($udpclient -ne $null) {
			$udpclient.Close()
		}
	}
} else {
	# $SavePath = Resolve-Path $SavePath
	try {
		$SavePath = Resolve-Path $SavePath
		if (-not (Test-Path $SavePath)) {
			New-Item -ItemType Directory -Path $SavePath -Force | Out-Null
		}

		$listener = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Any, $Port)
		$listener.Start()

		$localip = (Get-NetIPAddress | Where-Object { $_.AddressFamily -eq "IPv4" -and $_.PrefixOrigin -eq "Dhcp" }).IPAddress
		Write-Host "ip = $localip"
	
		Write-Host "Listening for file transfers on port $Port. Press Ctrl+C to stop."

		$client = $listener.AcceptTcpClient()
		$stream = $client.GetStream()

		# Receive file name
		$fileNameLengthBytes = New-Object byte[] 4
		$stream.Read($fileNameLengthBytes, 0, 4) | Out-Null
		$fileNameLength = [BitConverter]::ToInt32($fileNameLengthBytes, 0)
		$fileNameBytes = New-Object byte[] $fileNameLength
		$stream.Read($fileNameBytes, 0, $fileNameLength) | Out-Null
		$fileName = [System.Text.Encoding]::UTF8.GetString($fileNameBytes)

		# Receive file size
		$fileSizeBytes = New-Object byte[] 8
		$stream.Read($fileSizeBytes, 0, 8) | Out-Null
		$fileSize = [BitConverter]::ToInt64($fileSizeBytes, 0)

		$filePath = Join-Path $SavePath $fileName
		Write-Host "writing to $filePath"
		$fileStream = [System.IO.File]::Create($filePath)

		$buffer = New-Object byte[] 4096
		$totalBytesRead = 0

		while ($totalBytesRead -lt $fileSize) {
			$bytesRead = $stream.Read($buffer, 0, [Math]::Min($buffer.Length, $fileSize - $totalBytesRead))
			$fileStream.Write($buffer, 0, $bytesRead)
			$totalBytesRead += $bytesRead
			$percentComplete = [math]::Round(($totalBytesRead / $fileSize) * 100, 2)
			Write-Progress -Activity "Receiving File" -Status "$percentComplete% Complete" -PercentComplete $percentComplete
		}

		$fileStream.Close()
		Write-Host "File received successfully: $filePath"
		$client.Close()
	}
	catch {
		Write-Host "Error receiving file: $_"
	}
	finally {
		if ($fileStream) { $fileStream.Close() }
		if ($listener) { $listener.Stop() }
	}
}
