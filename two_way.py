import http.server
import socket
import socketserver
import os
import urllib
import zipfile
import io
import cgi

# Assign the appropriate port value and folder path
PORT = 8011
PATH = 'C:/Users/ArushWindows/OneDrive/Desktop/Sharing_Folder'
# Change the directory to access the files desktop
desktop = os.path.join(PATH)
os.chdir(desktop)

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def list_directory(self, path):
        try:
            # Generate directory listing
            items = os.listdir(path)
            items.sort(key=lambda a: a.lower())
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <head>
                    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
                    <style>
                        body {
                            font-family: Arial, sans-serif;
                            background-color: #f4f4f4;
                            margin: 0;
                            padding: 20px;
                        }
                        h1, h2 {
                            color: #333;
                        }
                        h2 {
                            margin-top: 40px;
                        }
                        ul {
                            list-style-type: none;
                            padding: 0;
                        }
                        li {
                            padding: 10px 0;
                            display: flex;
                            align-items: center;
                            justify-content: space-between;
                            border-bottom: 1px solid #ddd;
                        }
                        a {
                            color: #007bff;
                            text-decoration: none;
                        }
                        a:hover {
                            text-decoration: underline;
                        }
                        .folder, .file {
                            flex-grow: 1;
                        }
                        .download-icon {
                            color: #007bff;
                            margin-left: 10px;
                            cursor: pointer;
                        }
                        .download-icon:hover {
                            color: #0056b3;
                        }
                        .upload-form {
                            display: flex;
                            align-items: center;
                            margin-bottom: 20px;
                        }
                        .upload-form input[type="file"] {
                            margin-right: 10px;
                        }
                        .upload-form input[type="submit"] {
                            background-color: #007bff;
                            color: white;
                            border: none;
                            padding: 5px 10px;
                            cursor: pointer;
                            border-radius: 3px;
                        }
                        .upload-form input[type="submit"]:hover {
                            background-color: #0056b3;
                        }
                        .status-message {
                            margin-top: 20px;
                            color: #ff0000;
                            font-weight: bold;
                        }
                    </style>
                    <script>
                        function startFolderDownload(link, folderName) {
                            // Show "Compressing folder" message
                            document.getElementById("status").innerText = "Compressing folder: " + folderName;

                            // Create an iframe to start the download
                            var iframe = document.createElement("iframe");
                            iframe.style.display = "none";
                            iframe.src = link;
                            document.body.appendChild(iframe);

                            // Change the message to "Downloading" when the iframe loads (starts downloading)
                            iframe.onload = function() {
                                document.getElementById("status").innerText = "Downloading: " + folderName;
                            };
                        }
                    </script>
                </head>
                <body>
                    <h1>File Sharing</h1>
                    <h2>Upload a file</h2>
                    <form enctype="multipart/form-data" method="post" class="upload-form">
                        <input name="file" type="file" />
                        <input type="submit" value="Upload" />
                    </form>
                    <h2>Files and Folders</h2>
                    <ul>
            """)

            for item in items:
                full_path = os.path.join(path, item)
                encoded_item = urllib.parse.quote(item)

                if os.path.isdir(full_path):
                    # Show the folder with a link to navigate into it and a download icon
                    self.wfile.write(f'''
                        <li>
                            <span class="folder"><a href="{encoded_item}/"><i class="fas fa-folder"></i> {item}/</a></span>
                            <a href="javascript:void(0);" class="download-icon" onclick="startFolderDownload('{encoded_item}?download=zip', '{item}')">
                                <i class="fas fa-download"></i>
                            </a>
                        </li>
                    '''.encode())
                else:
                    # Show the file with a download link
                    self.wfile.write(f'''
                        <li>
                            <span class="file"><a href="{encoded_item}"><i class="fas fa-file"></i> {item}</a></span>
                            <a href="{encoded_item}" class="download-icon"><i class="fas fa-download"></i></a>
                        </li>
                    '''.encode())

            self.wfile.write(b'''
                    </ul>
                    <div id="status" class="status-message"></div>
                </body>
                </html>
            ''')
        except OSError:
            self.send_error(404, "Directory not found")

    def do_GET(self):
        if self.path.endswith('?download=zip'):
            # Handle folder zipping and downloading
            folder_name = urllib.parse.unquote(self.path.split('?')[0][1:])
            folder_path = os.path.join(desktop, folder_name)

            if os.path.isdir(folder_path):
                # Create a zip file in memory
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for root, dirs, files in os.walk(folder_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, os.path.join(folder_path, '..'))
                            zip_file.write(file_path, arcname)

                # Serve the zip file for download
                zip_buffer.seek(0)
                self.send_response(200)
                self.send_header('Content-type', 'application/zip')
                self.send_header('Content-Disposition', f'attachment; filename="{folder_name}.zip"')
                self.end_headers()
                self.wfile.write(zip_buffer.read())
            else:
                self.send_error(404, "Folder not found")
        else:
            # Serve files normally or navigate into folders
            super().do_GET()

    def do_POST(self):
        # Parse the form data posted
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST'}
        )

        # Extract the file field from the form
        file_field = form['file']

        # Check if the file field is present
        if file_field.filename:
            # Save the file
            file_path = os.path.join(os.getcwd(), file_field.filename)
            with open(file_path, 'wb') as output_file:
                output_file.write(file_field.file.read())

            # Send response back to the client
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"File uploaded successfully.<br><a href='/'>Go back</a>")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"No file was uploaded.<br><a href='/'>Go back</a>")

# Finding the IP address of the PC
hostname = socket.gethostname()
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
IP = "http://" + s.getsockname()[0] + ":" + str(PORT)
s.close()

# Creating the HTTP request and serving the folder in the specified PORT
with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
    print("Serving at port", PORT)
    print("Type this in your Browser", IP)
    httpd.serve_forever()
