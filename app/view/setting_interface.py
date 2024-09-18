# coding:utf-8
from qfluentwidgets import (SettingCardGroup, SwitchSettingCard, FolderListSettingCard,
                            OptionsSettingCard, PushSettingCard,
                            HyperlinkCard, PrimaryPushSettingCard, ScrollArea,
                            ComboBoxSettingCard, ExpandLayout, Theme, CustomColorSettingCard,
                            setTheme, setThemeColor, RangeSettingCard, isDarkTheme, SettingCard)
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import InfoBar
from PySide6.QtCore import Qt, Signal, QUrl, QStandardPaths
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QWidget, QLabel, QFileDialog

from ..common.config import cfg, HELP_URL, FEEDBACK_URL, AUTHOR, VERSION, YEAR, isWin11
from ..common.signal_bus import signalBus
from ..common.style_sheet import StyleSheet
from loguru import logger


class SettingInterface(ScrollArea):
    """ Setting interface """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        # setting label
        self.settingLabel = QLabel(self.tr("Settings"), self)
        self.GeneralGroup = SettingCardGroup(self.tr('常用设置'), self.scrollWidget)

        self.APIAutoStartEnable = SwitchSettingCard(
            FIF.TRANSPARENT,
            self.tr('自动启动API'),
            self.tr('程序启动时会自动启动API服务，请确保端口没有被占用。'),
            cfg.api_autostart,
            self.GeneralGroup
        )
        self.APIAutoStartEnable.checkedChanged.connect(cfg.save)

        self.Host = SettingCard(
            FIF.GLOBE,
            self.tr('主机'),
            self.tr('请输入API服务器的IP地址，如0.0.0.0'),
            self.GeneralGroup
        )
        self.Port = SettingCard(
            FIF.GLOBE,
            self.tr('端口'),
            self.tr('请输入API服务器的IP地址，如80'),
            self.GeneralGroup
        )

        self.TempDir = PushSettingCard(
            self.tr('临时文件目录'),
            FIF.FOLDER,
            self.tr("用于存放API生成的临时文件"),
            cfg.get(cfg.output_dir),
            self.GeneralGroup
        )
        self.ModelDir = PushSettingCard(
            self.tr('模型存放目录'),
            FIF.FOLDER,
            self.tr("用于存放各个引擎的模型文件"),
            cfg.get(cfg.model_dir),
            self.GeneralGroup
        )

        self.GeneralGroup.addSettingCard(self.APIAutoStartEnable)
        self.GeneralGroup.addSettingCard(self.Host)
        self.GeneralGroup.addSettingCard(self.Port)
        self.GeneralGroup.addSettingCard(self.TempDir)
        self.GeneralGroup.addSettingCard(self.ModelDir)

        # music folders
        self.ChatTTSCGroup = SettingCardGroup(
            self.tr("ChatTTS"), self.scrollWidget)

        self.ChatTTSEnable = SwitchSettingCard(
            FIF.TRANSPARENT,
            self.tr('启用ChatTTS'),
            self.tr('2noise团队开源的擅长对话的TTS大模型，基于AGPL协议。'),
            cfg.chattts_enable,
            self.ChatTTSCGroup
        )

        self.ChatTTSRepoFolderCard = PushSettingCard(
            self.tr('ChatTTS代码目录'),
            FIF.FOLDER,
            self.tr("ChatTTS代码目录"),
            cfg.get(cfg.chattts_dir),
            self.ChatTTSCGroup
        )

        self.ChatTTSModelFolderCard = PushSettingCard(
            self.tr('ChatTTS模型目录'),
            FIF.FOLDER,
            self.tr("ChatTTS模型目录'"),
            cfg.get(cfg.chattts_model),
            self.ChatTTSCGroup
        )

        # personalization
        self.personalGroup = SettingCardGroup(
            self.tr('Personalization'), self.scrollWidget)
        self.micaCard = SwitchSettingCard(
            FIF.TRANSPARENT,
            self.tr('Mica effect'),
            self.tr('Apply semi transparent to windows and surfaces'),
            cfg.micaEnabled,
            self.personalGroup
        )
        self.themeCard = OptionsSettingCard(
            cfg.themeMode,
            FIF.BRUSH,
            self.tr('Application theme'),
            self.tr("Change the appearance of your application"),
            texts=[
                self.tr('Light'), self.tr('Dark'),
                self.tr('Use system setting')
            ],
            parent=self.personalGroup
        )
        self.themeColorCard = CustomColorSettingCard(
            cfg.themeColor,
            FIF.PALETTE,
            self.tr('Theme color'),
            self.tr('Change the theme color of you application'),
            self.personalGroup
        )
        self.zoomCard = OptionsSettingCard(
            cfg.dpiScale,
            FIF.ZOOM,
            self.tr("Interface zoom"),
            self.tr("Change the size of widgets and fonts"),
            texts=[
                "100%", "125%", "150%", "175%", "200%",
                self.tr("Use system setting")
            ],
            parent=self.personalGroup
        )
        self.languageCard = ComboBoxSettingCard(
            cfg.language,
            FIF.LANGUAGE,
            self.tr('Language'),
            self.tr('Set your preferred language for UI'),
            texts=['简体中文', '繁體中文', 'English', self.tr('Use system setting')],
            parent=self.personalGroup
        )

        # material
        self.materialGroup = SettingCardGroup(
            self.tr('Material'), self.scrollWidget)
        self.blurRadiusCard = RangeSettingCard(
            cfg.blurRadius,
            FIF.ALBUM,
            self.tr('Acrylic blur radius'),
            self.tr('The greater the radius, the more blurred the image'),
            self.materialGroup
        )

        # update software
        self.updateSoftwareGroup = SettingCardGroup(
            self.tr("Software update"), self.scrollWidget)
        self.updateOnStartUpCard = SwitchSettingCard(
            FIF.UPDATE,
            self.tr('Check for updates when the application starts'),
            self.tr('The new version will be more stable and have more features'),
            configItem=cfg.checkUpdateAtStartUp,
            parent=self.updateSoftwareGroup
        )

        # application
        self.aboutGroup = SettingCardGroup(self.tr('About'), self.scrollWidget)
        self.helpCard = HyperlinkCard(
            HELP_URL,
            self.tr('打开在线文档'),
            FIF.HELP,
            self.tr('Help'),
            self.tr(
                '如果遇到问题，可以去在线文档看看'),
            self.aboutGroup
        )
        self.aboutCard = PrimaryPushSettingCard(
            self.tr('Check update'),
            FIF.INFO,
            self.tr('About'),
            '© ' + self.tr('Copyright') + f" {YEAR}, {AUTHOR}. " +
            self.tr('Version') + " " + VERSION,
            self.aboutGroup
        )

        self.__initWidget()

    def __initWidget(self):
        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 80, 0, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setObjectName('settingInterface')

        # initialize style sheet
        self.scrollWidget.setObjectName('scrollWidget')
        self.settingLabel.setObjectName('settingLabel')
        StyleSheet.SETTING_INTERFACE.apply(self)

        self.micaCard.setEnabled(isWin11())

        # initialize layout
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        self.settingLabel.move(36, 30)

        # add cards to group
        self.ChatTTSCGroup.addSettingCard(self.ChatTTSEnable)
        self.ChatTTSCGroup.addSettingCard(self.ChatTTSRepoFolderCard)
        self.ChatTTSCGroup.addSettingCard(self.ChatTTSModelFolderCard)

        self.personalGroup.addSettingCard(self.micaCard)
        self.personalGroup.addSettingCard(self.themeCard)
        self.personalGroup.addSettingCard(self.themeColorCard)
        self.personalGroup.addSettingCard(self.zoomCard)
        self.personalGroup.addSettingCard(self.languageCard)

        self.materialGroup.addSettingCard(self.blurRadiusCard)

        self.updateSoftwareGroup.addSettingCard(self.updateOnStartUpCard)

        self.aboutGroup.addSettingCard(self.helpCard)
        self.aboutGroup.addSettingCard(self.aboutCard)

        # add setting card group to layout
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(36, 10, 36, 0)
        self.expandLayout.addWidget(self.GeneralGroup)
        self.expandLayout.addWidget(self.ChatTTSCGroup)
        self.expandLayout.addWidget(self.personalGroup)
        self.expandLayout.addWidget(self.materialGroup)
        self.expandLayout.addWidget(self.updateSoftwareGroup)
        self.expandLayout.addWidget(self.aboutGroup)

    def __showRestartTooltip(self):
        """ show restart tooltip """
        InfoBar.success(
            self.tr('Updated successfully'),
            self.tr('Configuration takes effect after restart'),
            duration=1500,
            parent=self
        )

    def __onChatTTSModelFolderCardClicked(self):
        """ download folder card clicked slot """
        folder = QFileDialog.getExistingDirectory(
            self, self.tr("Choose folder"), "./")
        if not folder or cfg.get(cfg.chattts_model) == folder:
            return

        cfg.set(cfg.chattts_model, folder)
        self.ChatTTSModelFolderCard.setContent(folder)

    def __onChatTTSRepoFolderCardClicked(self):
        """ download folder card clicked slot """
        folder = QFileDialog.getExistingDirectory(
            self, self.tr("Choose folder"), "./")
        if not folder or cfg.get(cfg.chattts_dir) == folder:
            return

        cfg.set(cfg.chattts_dir, folder)
        self.ChatTTSRepoFolderCard.setContent(folder)

    def __onTempDirCardClicked(self):
        """ download folder card clicked slot """
        folder = QFileDialog.getExistingDirectory(
            self, self.tr("Choose folder"), "./")
        if not folder or cfg.get(cfg.output_dir) == folder:
            return

        cfg.set(cfg.output_dir, folder)
        self.TempDir.setContent(folder)

    def __onModelDirCardClicked(self):
        """ download folder card clicked slot """
        folder = QFileDialog.getExistingDirectory(
            self, self.tr("Choose folder"), "./")
        if not folder or cfg.get(cfg.output_dir) == folder:
            return

        cfg.set(cfg.model_dir, folder)
        self.ModelDir.setContent(folder)

    def __connectSignalToSlot(self):
        """ connect signal to slot """
        cfg.appRestartSig.connect(self.__showRestartTooltip)

        # ChatTTS
        self.ChatTTSModelFolderCard.clicked.connect(
            self.__onChatTTSModelFolderCardClicked)
        self.ChatTTSRepoFolderCard.clicked.connect(
            self.__onChatTTSRepoFolderCardClicked)

        # personalization
        self.themeCard.optionChanged.connect(lambda ci: setTheme(cfg.get(ci)))
        self.themeColorCard.colorChanged.connect(lambda c: setThemeColor(c))
        self.micaCard.checkedChanged.connect(signalBus.micaEnableChanged)
        self.ChatTTSEnable.checkedChanged.connect(cfg.save)
        self.TempDir.clicked.connect(self.__onTempDirCardClicked)
        self.ModelDir.clicked.connect(self.__onModelDirCardClicked)
