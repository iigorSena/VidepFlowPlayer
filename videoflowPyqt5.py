from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QMainWindow, QFileDialog, QListWidget, QHBoxLayout, QListWidgetItem, QProgressBar, QSlider, QTextEdit, QGraphicsDropShadowEffect
from PyQt5.QtGui import QFont, QIcon, QPixmap, QImage, QCursor, QMovie
from PyQt5.QtCore import QSize, QTimer, Qt, QThread, pyqtSignal
import sys
import os
import cv2
import vlc
from PyQt5 import QtWidgets

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

class VideoLoaderThread(QThread):
    videosLoaded = pyqtSignal(list)

    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path

    def run(self):
        video_extensions = ['.mp4', '.avi', '.mkv']
        video_files = []
        for file_name in os.listdir(self.folder_path):
            file_path = os.path.join(self.folder_path, file_name)
            if os.path.isfile(file_path) and any(file_name.lower().endswith(ext) for ext in video_extensions):
                video_files.append(file_name)
        self.videosLoaded.emit(video_files)

class VideoFlowPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.text_armazenamento = ""  # Variável para armazenar o texto
        self.video_files = []
        self.player_window = None  # Referência para a janela do player
  
    def initUI(self):
        self.setWindowTitle('VideoFlow Player')
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background-color: black; color: white;")

        # Label do título
        title_label = QLabel('VideoFlow Player', self)
        title_label.setFont(QFont('Helvetica', 18, QFont.Bold))
        title_label.setStyleSheet("color: white;")
        
        # Lista de vídeos
        self.video_list = QListWidget(self)
        self.video_list.itemDoubleClicked.connect(self.playSelectedVideo)
        self.video_list.setStyleSheet("background-color: #0F150F")

        # Caixa de Texto de avisos
        self.text_box = QTextEdit()
        self.text_box.setFixedWidth(350)
        self.text_box.setFont(QFont('Helvetica', 20))
        self.text_box.setPlaceholderText('Emitir aviso...')
        self.text_box.setAlignment(Qt.AlignTop)
        self.text_box.setLineWrapMode(QTextEdit.WidgetWidth)  # Permite que o texto quebre automaticamente
        self.text_box.setStyleSheet("QTextEdit { background-color: white; color: black; }")
        self.text_box.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)
       
         # Botão enviar aviso
        self.enviar_aviso_button = QPushButton('Enviar', self)
        self.enviar_aviso_button.setFont(QFont('Helvetica', 12))
        self.enviar_aviso_button.setStyleSheet("background-color: gray; color: white; border-radius: 15px")
        self.enviar_aviso_button.setFixedSize(280, 30)
        self.enviar_aviso_button.setCursor(QCursor(Qt.PointingHandCursor)) 
        self.enviar_aviso_button.clicked.connect(self.enviarAviso)  # Conecte ao método enviarAviso
        

        # Layout Box de aviso
        quadro_avisos = QVBoxLayout()
        quadro_avisos.addWidget(self.text_box)
        quadro_avisos.addWidget(self.enviar_aviso_button, alignment=Qt.AlignCenter)
        
        # Layout Box
        boxvideo_list_layout = QHBoxLayout()
        boxvideo_list_layout.addWidget(self.video_list)
        boxvideo_list_layout.addLayout(quadro_avisos)

        # Temporizador do vídeo
        self.time_label = QLabel('00:00 / 00:00', self)
        self.time_label.setFont(QFont('Helvetica', 12))
        self.time_label.setStyleSheet("color: white;")

        # Botão Volume
        self.mute_button = QPushButton(self)
        self.mute_button.setIcon(QIcon(resource_path('img/volume-on.png')))  # Defina o ícone inicial
        self.mute_button.setIconSize(QSize(30, 30))
        self.mute_button.setFixedSize(40, 40)
        self.mute_button.setStyleSheet("background-color: black; color: white;")
        self.mute_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.mute_button.clicked.connect(self.toggleMute)  # Conecte ao método toggleMute

        # Controle deslizante de volume
        self.volume_slider = QSlider(Qt.Horizontal, self)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(50) 
        self.volume_slider.setToolTip('Volume')
        self.volume_slider.setFixedWidth(150)
        self.volume_slider.valueChanged.connect(self.setVolume)  # Conecte ao método setVolume

        # Barra de progresso do vídeo
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                color: white; 
                border: 1px solid grey; 
                border-radius: 5px; 
                background-color: black;
                height: 5px;
            }
            QProgressBar::chunk {
                background-color: #007BFF;
                border-radius: 5px;
            }
        """)
        self.progress_bar.setTextVisible(False)

        # Layout Time/Volume/BarProgess
        time_volume_layout = QHBoxLayout()
        time_volume_layout.addWidget(self.time_label)
        time_volume_layout.addWidget(self.mute_button)
        time_volume_layout.addWidget(self.volume_slider)
        time_volume_layout.addStretch(1)  # Adiciona espaço flexível para empurrar widgets para a esquerda
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(self.progress_bar)

        # Botões de controle de vídeo
        control_layout = QHBoxLayout()
        self.prev_button = QPushButton(self)
        self.prev_button.setIcon(QIcon(resource_path('img/retroceder-button.png')))
        self.prev_button.setIconSize(QSize(50, 50))
        self.prev_button.setFixedSize(60, 60)
        self.prev_button.setStyleSheet("background-color: black; color: white;")
        self.prev_button.setCursor(QCursor(Qt.PointingHandCursor))  # Define o cursor para a mãozinha

        self.play_pause_button = QPushButton(self)
        self.play_pause_button.setIcon(QIcon(resource_path('img/play-button.png')))
        self.play_pause_button.setIconSize(QSize(50, 50))
        self.play_pause_button.setFixedSize(60, 60)
        self.play_pause_button.setStyleSheet("background-color: black; color: white;")
        self.play_pause_button.setEnabled(False)  # Desativa o botão inicialmente
        self.play_pause_button.setCursor(QCursor(Qt.PointingHandCursor))  # Define o cursor para a mãozinha

        self.next_button = QPushButton(self)
        self.next_button.setIcon(QIcon(resource_path('img/avancar-button.png')))
        self.next_button.setIconSize(QSize(50, 50))
        self.next_button.setFixedSize(60, 60)
        self.next_button.setStyleSheet("background-color: black; color: white;")
        self.next_button.setCursor(QCursor(Qt.PointingHandCursor))  # Define o cursor para a mãozinha

        self.prev_button.clicked.connect(self.prevVideo)
        self.play_pause_button.clicked.connect(self.playPauseVideo)
        self.next_button.clicked.connect(self.nextVideo)
        control_layout.addWidget(self.prev_button)
        control_layout.addWidget(self.play_pause_button)
        control_layout.addWidget(self.next_button)
        #control_layout.addStretch(1)

        #3° Espaço para centralização layout control
        espaco_layout = QHBoxLayout()
        quadrado = QLabel()
        quadrado.setFixedWidth(100)
        quadrado.setStyleSheet("background-color: black")
        espaco_layout.addWidget(quadrado)
        espaco_layout.addStretch(1)
             

        # Botão para abrir a pasta
        self.open_folder_button = QPushButton('Abrir Pasta', self)
        self.open_folder_button.clicked.connect(self.openFolder)
        self.open_folder_button.setFont(QFont('Helvetica', 14))
        self.open_folder_button.setStyleSheet("background-color: #007BFF; color: white; border-radius: 15px")
        self.open_folder_button.setFixedSize(250, 40)
        self.open_folder_button.setCursor(QCursor(Qt.PointingHandCursor))  # Define o cursor para a mãozinha       

        # Pop-up de carregamento
        self.loading_popup = QLabel('Aguarde carregando vídeos...', self)
        self.loading_popup.setFixedSize(300, 150)  # Define o tamanho do pop-up
        self.loading_popup.setStyleSheet("background-color: white; color: black; border: 1px solid gray; border-radius: 10px")
        self.loading_popup.setFont(QFont('Helvetica', 16))
        self.loading_popup.setAlignment(Qt.AlignCenter)

        self.loading_popup.setVisible(False)

        #Layout Horizontal Time_Volume & Control_Buttons
        folder_control_layout = QHBoxLayout()
        folder_control_layout.addLayout(time_volume_layout)
        folder_control_layout.addLayout(control_layout)
        folder_control_layout.addLayout(espaco_layout)

        # Layout horizontal para centralizar o botão
        folder_button_layout = QHBoxLayout()
        folder_button_layout.addStretch(1)
        folder_button_layout.addWidget(self.open_folder_button)
        folder_button_layout.addStretch(1)

        # Layout vertical para organizar os widgets da janela principal
        layout = QVBoxLayout()
        layout.addWidget(title_label)
        layout.addLayout(boxvideo_list_layout)
        layout.addWidget(self.loading_popup, alignment=Qt.AlignCenter)  # Adiciona o pop-up centralizado
        layout.addLayout(folder_control_layout)
        layout.addLayout(progress_layout)  # Adiciona o layout de progresso
        layout.addLayout(folder_button_layout)  # Adiciona o botão centralizado

        # Widget central para o layout da janela principal
        central_widget = QWidget(self)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        
    def openFolder(self):
        folder_path = QFileDialog.getExistingDirectory(self, 'Selecionar Pasta de Vídeos')
        if folder_path:
            self.loading_popup.setVisible(True)
            # Centralizando o pop-up dentro da video_list
            list_rect = self.video_list.geometry()
            popup_width = self.loading_popup.width()
            popup_height = self.loading_popup.height()
            popup_x = list_rect.x() + (list_rect.width() - popup_width) // 2
            popup_y = list_rect.y() + (list_rect.height() - popup_height) // 2
            self.loading_popup.move(popup_x, popup_y)

            self.folder_path = folder_path
            self.video_loader_thread = VideoLoaderThread(folder_path)  # carrega os vídeos da pasta selecionada
            self.video_loader_thread.videosLoaded.connect(self.onVideosLoaded)
            self.video_loader_thread.start()
                        
    def onVideosLoaded(self, video_files):
        self.loading_popup.setVisible(False)
        self.video_files = video_files
        self.displayVideoList()

    def getVideoFiles(self, folder_path):
        video_extensions = ['.mp4', '.avi', '.mkv']  # Extensões de vídeo suportadas
        video_files = []
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)
            if os.path.isfile(file_path) and any(file_name.lower().endswith(ext) for ext in video_extensions):
                video_files.append(file_name)
        return video_files

    def displayVideoList(self):
        self.video_list.clear()
        for idx, video_file in enumerate(self.video_files):
            video_path = os.path.join(self.folder_path, video_file)
            
            # Crie um widget para o item da lista
            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(0, 10, 0, 0)  # Remove as margens
            item_layout.setSpacing(5)  # Espaçamento entre os widgets

            # 1ª Coluna: Número da ordem do vídeo
            order_label = QLabel(str(idx + 1))
            order_label.setFont(QFont('Helvetica', 12))
            order_label.setFixedWidth(50)
            item_layout.addWidget(order_label, Qt.AlignCenter)

            # 2ª Coluna: Miniatura do vídeo
            thumbnail_path = self.getVideoThumbnail(video_path)
            if thumbnail_path:
                icon_label = QLabel()
                pixmap = QPixmap(thumbnail_path).scaledToWidth(120)  # Redimensiona a miniatura para 120 pixels de largura
                icon_label.setPixmap(pixmap)
                icon_label.setFixedWidth(120)
                item_layout.addWidget(icon_label, Qt.AlignCenter)

            # 3ª Coluna: Nome do vídeo
            video_name_label = QLabel(video_file)
            video_name_label.setFont(QFont('Helvetica', 12))
            video_name_label.setCursor(QCursor(Qt.PointingHandCursor))  # Define o cursor para a mãozinha
            video_name_label.setMinimumWidth(100)
            item_layout.addWidget(video_name_label, Qt.AlignCenter)

            # 4ª Coluna: Tempo total do vídeo
            total_time_label = QLabel(self.getVideoDuration(video_path))
            total_time_label.setFont(QFont('Helvetica', 12))
            total_time_label.setMaximumWidth(100)
            item_layout.addWidget(total_time_label, Qt.AlignCenter)

            """# 5 Coluna
            empty_label = QLabel()
            empty_label.setFont(QFont('Helvetica', 12))
            empty_label.setMaximumWidth(300)
            item_layout.addWidget(empty_label, Qt.AlignCenter)"""
            
            item_widget.setLayout(item_layout)
            
            # Crie um item da lista e adicione o widget
            item = QListWidgetItem()
            item.setSizeHint(item_widget.sizeHint())
            self.video_list.addItem(item)
            self.video_list.setItemWidget(item, item_widget)

    def getVideoDuration(self, video_path):
        video = cv2.VideoCapture(video_path)
        if video.isOpened():
            frames = video.get(cv2.CAP_PROP_FRAME_COUNT)
            fps = video.get(cv2.CAP_PROP_FPS)
            seconds = int(frames / fps)
            return self.formatTime(seconds)
        return "00:00"

    def getVideoThumbnail(self, video_path):
        # Captura um frame do vídeo usando OpenCV para obter uma miniatura
        cap = cv2.VideoCapture(video_path)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                # Converte o frame para formato QImage
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
                # Salva o frame temporário
                thumbnail_path = 'temp_thumbnail.png'
                image.save(thumbnail_path)
                return thumbnail_path
            cap.release()
        else:
            print("A captura das thumbs falhou falhou")
            return None

    def playSelectedVideo(self, item):
        video_widget = self.video_list.itemWidget(item)
        video_name_label = video_widget.layout().itemAt(2).widget()
        video_name = video_name_label.text()
        video_path = os.path.join(self.folder_path, video_name)
        if self.player_window:
            self.player_window.playVideo(video_path)
            self.play_pause_button.setEnabled(True)  # Ativa o botão quando um vídeo é selecionado
            self.play_pause_button.setIcon(QIcon(resource_path('img/pause-button.png')))  # Define o ícone para pause
            self.updateTimeLabel()  # Atualiza a barra de tempo
            self.progress_bar.setValue(0)  # Reinicia a barra de progresso

    def prevVideo(self):
        current_row = self.video_list.currentRow()
        if current_row > 0:
            self.video_list.setCurrentRow(current_row - 1)
            self.playSelectedVideo(self.video_list.currentItem())
        self.updateTimeLabel()

    def nextVideo(self):
        current_row = self.video_list.currentRow()
        if current_row < self.video_list.count() - 1:
            self.video_list.setCurrentRow(current_row + 1)
            self.playSelectedVideo(self.video_list.currentItem())
        else:
            print("=> Todos os vídeos foram reproduzidos.")


    def playPauseVideo(self):
        if self.player_window:
            if self.player_window.is_playing:
                self.player_window.player.pause()
                self.play_pause_button.setIcon(QIcon(resource_path('img/play-button.png')))  # Alterar ícone para play
                self.player_window.is_playing = False
            else:
                self.player_window.player.play()
                self.play_pause_button.setIcon(QIcon(resource_path('img/pause-button.png')))  # Alterar ícone para pause
                self.player_window.is_playing = True
            self.updateTimeLabel()  # Atualiza a barra de tempo

    def updateTimeLabel(self):
        if self.player_window and self.player_window.media:
            current_time = self.player_window.player.get_time() // 1000
            total_time = self.player_window.player.get_length() // 1000
             # Verificação para evitar valores negativos
            if current_time < 0:
                current_time = 0
            if total_time < 0:
                total_time = 0

            self.time_label.setText(f'{self.formatTime(current_time)} / {self.formatTime(total_time)}')
            
            if total_time > 0:
                progress = int((current_time / total_time) * 100)
                self.progress_bar.setValue(progress)
            
            if total_time > 0 and (total_time - current_time) <= 0.3:
                 self.nextVideo()
            else:
                QTimer.singleShot(300, self.updateTimeLabel)  # Atualiza a cada 50 milissegundos
            
        

    def formatTime(self, seconds):
        minutes = seconds // 60
        seconds = seconds % 60
        return f'{minutes:02}:{seconds:02}'
    
    def toggleMute(self):
        if self.player_window:
            is_muted = self.player_window.player.audio_get_mute()
            self.player_window.player.audio_set_mute(not is_muted)
            if is_muted:
                self.mute_button.setIcon(QIcon(resource_path('img/volume-on.png')))
            else:
                self.mute_button.setIcon(QIcon(resource_path('img/volume-off.png')))


    def setVolume(self, value):
        if self.player_window:
            self.player_window.player.audio_set_volume(value)

    def enviarAviso(self):
        self.text_armazenamento = self.text_box.toPlainText()
        self.player_window.showPopupAviso(self.text_armazenamento)
        self.text_box.clear()

#-------------------------------------Back-End--------------------------------------------
#-------------------------------------Back-End--------------------------------------------

class VideoPlayerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Janela do Player')
        self.setGeometry(100, 100, 800, 600)

        # Configura o player de vídeo usando VLC
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()

        # Widget para exibir o player de vídeo
        self.player_widget = QtWidgets.QFrame(self)
        self.player_widget.setGeometry(0, 0, 800, 600)

        # Layout horizontal para o player de vídeo
        layout = QHBoxLayout()
        layout.addWidget(self.player_widget)
        self.setLayout(layout)

        # Pop-up de aviso
        self.popup_aviso = QLabel('Funcionou!', self)
        self.popup_aviso.setStyleSheet("background-color: white; color: black; border: 1px solid gray; border-radius: 10px")
        self.popup_aviso.setFont(QFont('Helvetica', 25))
        self.popup_aviso.setAlignment(Qt.AlignCenter)
        self.popup_aviso.setVisible(False)  # Inicialmente invisível

        # Inicia a reprodução
        self.media = None
        self.is_playing = False

    def playVideo(self, video_path):
        if self.is_playing:
            self.player.stop()
        self.media = self.instance.media_new(video_path)
        self.player.set_media(self.media)
        self.player.set_hwnd(self.player_widget.winId())
        self.player.play()
        self.is_playing = True

    def showPopupAviso(self, text):
        popup_height = int(self.height() * 1)
        self.popup_aviso.setText(text)
        self.popup_aviso.setStyleSheet("""
            background-color: white; 
            color: black;             
        """)
        # Configuração do efeito de sombra
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setBlurRadius(25)  # Ajuste o valor conforme necessário
        shadow_effect.setOffset(-10, 0)  # Direção da sombra (esquerda)
        shadow_effect.setColor(Qt.gray)  # Cor da sombra
        # Aplicar o efeito de sombra ao pop-up
        self.popup_aviso.setGraphicsEffect(shadow_effect)
        self.popup_aviso.setFixedSize(500, popup_height)
        self.popup_aviso.move((self.width() - self.popup_aviso.width()) // 1, (self.height() - self.popup_aviso.height()) // 2)
        self.popup_aviso.setVisible(True)
        QTimer.singleShot(5000, self.popup_aviso.hide)  # Pop-up desaparece após 5 segundos

    def resizeEvent(self, event):
        # Atualiza o tamanho do pop-up quando a janela é redimensionada
        popup_height = int(self.height() * 1)  # Altura do pop-up como 50% da altura da janela
        self.popup_aviso.setFixedSize(500, popup_height)  # Ajuste o valor 200 para a largura desejada
        self.popup_aviso.move(self.width() - self.popup_aviso.width(), 0)
        super().resizeEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    player_main = VideoFlowPlayer()
    player_main.showMaximized()

    player_window = VideoPlayerWindow()
    player_window.showMaximized()

    # Passando a referência da janela do player para a janela principal
    player_main.player_window = player_window

    sys.exit(app.exec_())
