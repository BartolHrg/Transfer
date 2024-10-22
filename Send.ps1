

param(
    [Parameter(Mandatory=$true)]
    [string]$ReceiverIP,
    
    [Parameter(Mandatory=$true)]
    [int]$Port,
    
    [Parameter(Mandatory=$true)]
	[ValidateSet('f', 'm')]
    [string]$typ,
    
    [Parameter(Mandatory=$true)]
    [string]$FilePath
)

if ($typ -eq "m") {
	try {
		$endpoint = New-Object System.Net.IPEndPoint([IPAddress]::Parse($ReceiverIP), $Port)
		$udpclient = New-Object System.Net.Sockets.UdpClient
		$encodedMessage = [Text.Encoding]::ASCII.GetBytes($FilePath)
		$bytesSent = $udpclient.Send($encodedMessage, $encodedMessage.Length, $endpoint)
		Write-Host "Message sent successfully. Bytes sent: $bytesSent"
	}
	catch {
		Write-Host "Error sending message: $_"
	}
	finally {
		if ($udpclient -ne $null) {
			$udpclient.Close()
		}
	}
} else {
	try {
		$FilePath = Resolve-Path $FilePath
		if (-not (Test-Path $FilePath)) {
			throw "File not found: $FilePath"
		}

		$client = New-Object System.Net.Sockets.TcpClient($ReceiverIP, $Port)
		$stream = $client.GetStream()

		$fileInfo = Get-Item $FilePath
		$fileName = $fileInfo.Name
		$fileSize = $fileInfo.Length

		$fileNameBytes = [System.Text.Encoding]::UTF8.GetBytes($fileName)
		$stream.Write([BitConverter]::GetBytes($fileNameBytes.Length), 0, 4)
		$stream.Write($fileNameBytes, 0, $fileNameBytes.Length)

		$stream.Write([BitConverter]::GetBytes($fileSize), 0, 8)

		$buffer = New-Object byte[] 4096
		$fileStream = [System.IO.File]::OpenRead($FilePath)
		$bytesRead = 0
		$totalBytesRead = 0

		while (($bytesRead = $fileStream.Read($buffer, 0, $buffer.Length)) -gt 0) {
			$stream.Write($buffer, 0, $bytesRead)
			$totalBytesRead += $bytesRead
			$percentComplete = [math]::Round(($totalBytesRead / $fileSize) * 100, 2)
			Write-Progress -Activity "Sending File" -Status "$percentComplete% Complete" -PercentComplete $percentComplete
		}

		Write-Host "File sent successfully: $fileName"
	}
	catch {
		Write-Host "Error sending file: $_"
	}
	finally {
		if ($fileStream) { $fileStream.Close() }
		if ($stream) { $stream.Close() }
		if ($client) { $client.Close() }
	}
}





