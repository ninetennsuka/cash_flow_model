#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простой веб-сервер с файловым менеджером
Локальный HTTP сервер для обмена файлами
"""

import http.server
import socketserver
import os
import urllib.parse
from pathlib import Path

class FileServerHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        """Обрабатывает GET запросы"""
        if self.path == '/':
            self.send_file_list()
        elif self.path.startswith('/download/'):
            self.download_file()
        else:
            super().do_GET()
    
    def do_POST(self):
        """Обрабатывает POST запросы (загрузка файлов)"""
        if self.path == '/upload':
            self.upload_file()
        else:
            self.send_error(404)
    
    def send_file_list(self):
        """Отправляет HTML страницу с файлами"""
        current_dir = Path(os.getcwd())
        files = []
        
        # Получаем список файлов
        for item in current_dir.iterdir():
            if item.is_file():
                size = item.stat().st_size
                size_str = self.format_size(size)
                files.append({
                    'name': item.name,
                    'size': size_str,
                    'is_file': True
                })
            elif item.is_dir():
                files.append({
                    'name': item.name,
                    'size': '[DIR]',
                    'is_file': False
                })
        
        # Сортируем: сначала папки, потом файлы
        files.sort(key=lambda x: (x['is_file'], x['name'].lower()))
        
        # Создаем HTML
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Файловый сервер</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                h1 { color: #333; }
                table { border-collapse: collapse; width: 100%; }
                th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background-color: #f2f2f2; }
                .dir { color: #0066cc; font-weight: bold; }
                .file { color: #333; }
                .size { color: #666; font-size: 0.9em; }
                .upload-form { margin: 20px 0; padding: 20px; background: #f9f9f9; border-radius: 5px; }
            </style>
        </head>
        <body>
            <h1>📁 Файловый сервер</h1>
            <p>Текущая папка: <strong>{}</strong></p>
            
            <div class="upload-form">
                <h3>📤 Загрузить файл</h3>
                <form method="post" action="/upload" enctype="multipart/form-data">
                    <input type="file" name="file" required>
                    <input type="submit" value="Загрузить">
                </form>
            </div>
            
            <table>
                <tr>
                    <th>Название</th>
                    <th>Размер</th>
                    <th>Действия</th>
                </tr>
        """.format(current_dir)
        
        for file_info in files:
            if file_info['is_file']:
                html += f"""
                <tr>
                    <td class="file">📄 {file_info['name']}</td>
                    <td class="size">{file_info['size']}</td>
                    <td><a href="/download/{urllib.parse.quote(file_info['name'])}">⬇️ Скачать</a></td>
                </tr>
                """
            else:
                html += f"""
                <tr>
                    <td class="dir">📁 {file_info['name']}</td>
                    <td class="size">{file_info['size']}</td>
                    <td>—</td>
                </tr>
                """
        
        html += """
            </table>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def download_file(self):
        """Отправляет файл для скачивания"""
        filename = urllib.parse.unquote(self.path[10:])  # убираем '/download/'
        filepath = Path(filename)
        
        if filepath.exists() and filepath.is_file():
            self.send_response(200)
            self.send_header('Content-type', 'application/octet-stream')
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
            self.end_headers()
            
            with open(filepath, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404, "Файл не найден")
    
    def upload_file(self):
        """Обрабатывает загрузку файла"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Простой парсинг multipart/form-data
            boundary = self.headers['Content-Type'].split('boundary=')[1].encode()
            parts = post_data.split(boundary)
            
            for part in parts:
                if b'filename=' in part:
                    # Извлекаем имя файла
                    header_section = part.split(b'\r\n\r\n')[0]
                    filename_start = header_section.find(b'filename="') + 10
                    filename_end = header_section.find(b'"', filename_start)
                    filename = header_section[filename_start:filename_end].decode('utf-8')
                    
                    if filename:
                        # Извлекаем содержимое файла
                        file_data = part.split(b'\r\n\r\n', 1)[1].rstrip(b'\r\n--')
                        
                        # Сохраняем файл
                        with open(filename, 'wb') as f:
                            f.write(file_data)
                        
                        print(f"✅ Загружен файл: {filename}")
                        break
            
            # Отправляем ответ
            self.send_response(302)
            self.send_header('Location', '/')
            self.end_headers()
            
        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
            self.send_error(500, "Ошибка загрузки файла")
    
    def format_size(self, size_bytes):
        """Форматирует размер файла"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"

def start_server(port=8000, directory=None):
    """Запускает файловый сервер"""
    if directory:
        os.chdir(directory)
        print(f"📁 Рабочая папка: {os.getcwd()}")
    
    handler = FileServerHandler
    
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            print(f"🌐 Сервер запущен на порту {port}")
            print(f"🔗 Откройте в браузере: http://localhost:{port}")
            print("Нажмите Ctrl+C для остановки сервера")
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n⏹️ Сервер остановлен")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Порт {port} уже используется")
        else:
            print(f"❌ Ошибка запуска сервера: {e}")

def main():
    print("=== ФАЙЛОВЫЙ ВЕБ-СЕРВЕР ===\n")
    
    try:
        port = int(input("Порт (по умолчанию 8000): ") or "8000")
        directory = input("Рабочая папка (по умолчанию текущая): ").strip()
        
        if directory and not os.path.exists(directory):
            print(f"❌ Папка не существует: {directory}")
            return
        
        start_server(port, directory if directory else None)
        
    except ValueError:
        print("❌ Некорректный номер порта")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()
