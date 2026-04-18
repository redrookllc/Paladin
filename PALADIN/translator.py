"""
translator.py  —  Paladin GUI Translator
============================================
Supports: English (default), Arabic (ar), French (fr),
          Spanish (es), German (de), Chinese Simplified (zh), Japanese (ja)

Usage (one line in main.py after QApplication is created):
    from translator import install_translator; install_translator(app, "ar")

How it works:
  • Walks every QWidget in the entire application tree after the window is shown.
  • Replaces all visible text (QLabel, QPushButton, QCheckBox, QGroupBox,
    QLineEdit placeholders, QTextEdit placeholders, QTableWidget headers,
    QTabBar tab text, window titles) using the STRINGS dictionary.
  • RTL layout is applied automatically for Arabic.
  • A floating language-switcher toolbar is injected into the main window
    so the user can switch languages at runtime without restarting.
"""

from __future__ import annotations
import sys
from typing import Dict, Optional

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QCheckBox,
    QGroupBox, QLineEdit, QTextEdit, QTableWidget, QTabWidget,
    QAbstractItemView, QMainWindow, QToolBar, QComboBox, QAction,
    QSizePolicy,
)
from PyQt5.QtCore import Qt, QTimer, QObject, pyqtSignal
from PyQt5.QtGui import QFont

LANGUAGES: Dict[str, str] = {
    "en": "English",
    "ar": "العربية",
    "fr": "Français",
    "es": "Español",
    "de": "Deutsch",
    "zh": "中文",
    "ja": "日本語",
}

RTL_LANGS = {"ar"}

# key  = canonical English string (strip/lower for matching)
# value = dict of lang_code → translated string

_T: Dict[str, Dict[str, str]] = {

    "red rook": {
        "ar": "الرخ الأحمر", "fr": "Tour Rouge", "es": "Torre Roja",
        "de": "Roter Turm", "zh": "红车", "ja": "レッドルーク",
    },
    "trading platform": {
        "ar": "منصة التداول", "fr": "Plateforme de Trading", "es": "Plataforma de Trading",
        "de": "Handelsplattform", "zh": "交易平台", "ja": "取引プラットフォーム",
    },
    "ai-powered trading intelligence platform": {
        "ar": "منصة ذكاء التداول بالذكاء الاصطناعي",
        "fr": "Plateforme d'Intelligence de Trading IA",
        "es": "Plataforma de Inteligencia de Trading con IA",
        "de": "KI-gestützte Handelsintelligenzplattform",
        "zh": "AI驱动的交易智能平台",
        "ja": "AI搭載トレーディングインテリジェンスプラットフォーム",
    },
    "initialising engine…": {
        "ar": "جارٍ تهيئة المحرك…", "fr": "Initialisation du moteur…",
        "es": "Inicializando motor…", "de": "Motor wird initialisiert…",
        "zh": "正在初始化引擎…", "ja": "エンジンを初期化中…",
    },
    "lightgbm · isotonic calibration · 50+ technical features · pattern recognition": {
        "ar": "LightGBM · معايرة رتيبة · 50+ ميزة تقنية · التعرف على الأنماط",
        "fr": "LightGBM · Calibration Isotonique · 50+ Fonctionnalités · Reconnaissance de Patterns",
        "es": "LightGBM · Calibración Isotónica · 50+ Características · Reconocimiento de Patrones",
        "de": "LightGBM · Isotonische Kalibrierung · 50+ Merkmale · Mustererkennung",
        "zh": "LightGBM · 等渗校准 · 50+技术特征 · 模式识别",
        "ja": "LightGBM · アイソトニックキャリブレーション · 50+テクニカル特徴 · パターン認識",
    },

    "setup wizard": {
        "ar": "معالج الإعداد", "fr": "Assistant de Configuration",
        "es": "Asistente de Configuración", "de": "Einrichtungsassistent",
        "zh": "设置向导", "ja": "セットアップウィザード",
    },
    "select your trading personality to continue": {
        "ar": "اختر شخصيتك التجارية للمتابعة",
        "fr": "Sélectionnez votre personnalité de trading pour continuer",
        "es": "Seleccione su personalidad de trading para continuar",
        "de": "Wählen Sie Ihre Handelspersönlichkeit, um fortzufahren",
        "zh": "请选择您的交易个性以继续",
        "ja": "続けるには取引スタイルを選択してください",
    },
    "step 01 / 02": {
        "ar": "الخطوة 01 / 02", "fr": "Étape 01 / 02", "es": "Paso 01 / 02",
        "de": "Schritt 01 / 02", "zh": "步骤 01 / 02", "ja": "ステップ 01 / 02",
    },
    "step 02 / 02": {
        "ar": "الخطوة 02 / 02", "fr": "Étape 02 / 02", "es": "Paso 02 / 02",
        "de": "Schritt 02 / 02", "zh": "步骤 02 / 02", "ja": "ステップ 02 / 02",
    },
    "select your trading personality": {
        "ar": "اختر شخصيتك التجارية", "fr": "Sélectionnez votre personnalité de trading",
        "es": "Seleccione su personalidad de trading",
        "de": "Wählen Sie Ihre Handelspersönlichkeit",
        "zh": "选择您的交易个性", "ja": "取引スタイルを選択",
    },
    "your choice shapes your trading strategy and interface configuration.": {
        "ar": "اختيارك يشكل استراتيجية التداول وتهيئة الواجهة.",
        "fr": "Votre choix façonne votre stratégie de trading et la configuration de l'interface.",
        "es": "Su elección da forma a su estrategia de trading y configuración de interfaz.",
        "de": "Ihre Wahl prägt Ihre Handelsstrategie und Schnittstellenkonfiguration.",
        "zh": "您的选择将塑造您的交易策略和界面配置。",
        "ja": "選択はトレード戦略とインターフェース設定を形成します。",
    },
    "ready to begin": {
        "ar": "جاهز للبدء", "fr": "Prêt à commencer", "es": "Listo para comenzar",
        "de": "Bereit zu beginnen", "zh": "准备开始", "ja": "開始準備完了",
    },
    "review your configuration and launch the trading platform.": {
        "ar": "راجع إعداداتك وأطلق منصة التداول.",
        "fr": "Vérifiez votre configuration et lancez la plateforme de trading.",
        "es": "Revise su configuración y lance la plataforma de trading.",
        "de": "Überprüfen Sie Ihre Konfiguration und starten Sie die Handelsplattform.",
        "zh": "检查您的配置并启动交易平台。",
        "ja": "設定を確認してトレードプラットフォームを起動します。",
    },
    "platform features:": {
        "ar": "ميزات المنصة:", "fr": "Fonctionnalités de la plateforme :",
        "es": "Características de la plataforma:", "de": "Plattformfunktionen:",
        "zh": "平台功能：", "ja": "プラットフォーム機能：",
    },
    "← back": {
        "ar": "→ رجوع", "fr": "← Retour", "es": "← Atrás",
        "de": "← Zurück", "zh": "← 返回", "ja": "← 戻る",
    },
    "next →": {
        "ar": "← التالي", "fr": "Suivant →", "es": "Siguiente →",
        "de": "Weiter →", "zh": "下一步 →", "ja": "次へ →",
    },
    "launch platform": {
        "ar": "إطلاق المنصة", "fr": "Lancer la plateforme",
        "es": "Lanzar plataforma", "de": "Plattform starten",
        "zh": "启动平台", "ja": "プラットフォーム起動",
    },



    "markets": {
        "ar": "الأسواق", "fr": "Marchés", "es": "Mercados",
        "de": "Märkte", "zh": "市场", "ja": "マーケット",
    },
    "tools": {
        "ar": "الأدوات", "fr": "Outils", "es": "Herramientas",
        "de": "Werkzeuge", "zh": "工具", "ja": "ツール",
    },
    "system": {
        "ar": "النظام", "fr": "Système", "es": "Sistema",
        "de": "System", "zh": "系统", "ja": "システム",
    },
    "dashboard": {
        "ar": "لوحة التحكم", "fr": "Tableau de bord", "es": "Panel",
        "de": "Dashboard", "zh": "仪表盘", "ja": "ダッシュボード",
    },
    "signals": {
        "ar": "الإشارات", "fr": "Signaux", "es": "Señales",
        "de": "Signale", "zh": "信号", "ja": "シグナル",
    },
    "chart": {
        "ar": "الرسم البياني", "fr": "Graphique", "es": "Gráfico",
        "de": "Diagramm", "zh": "图表", "ja": "チャート",
    },
    "portfolio": {
        "ar": "المحفظة", "fr": "Portefeuille", "es": "Portafolio",
        "de": "Portfolio", "zh": "投资组合", "ja": "ポートフォリオ",
    },
    "journal": {
        "ar": "المذكرة", "fr": "Journal", "es": "Diario",
        "de": "Journal", "zh": "日记", "ja": "ジャーナル",
    },
    "risk calc": {
        "ar": "حساب المخاطر", "fr": "Calc. Risque", "es": "Calc. Riesgo",
        "de": "Risikorechner", "zh": "风险计算", "ja": "リスク計算",
    },
    "ai chat": {
        "ar": "دردشة الذكاء الاصطناعي", "fr": "Chat IA", "es": "Chat IA",
        "de": "KI-Chat", "zh": "AI聊天", "ja": "AIチャット",
    },
    "settings": {
        "ar": "الإعدادات", "fr": "Paramètres", "es": "Configuración",
        "de": "Einstellungen", "zh": "设置", "ja": "設定",
    },
    "watchlist": {
        "ar": "قائمة المراقبة", "fr": "Liste de surveillance",
        "es": "Lista de seguimiento", "de": "Beobachtungsliste",
        "zh": "观察列表", "ja": "ウォッチリスト",
    },

    "price chart": {
        "ar": "الرسم البياني للسعر", "fr": "Graphique des prix",
        "es": "Gráfico de precios", "de": "Preisdiagramm",
        "zh": "价格图表", "ja": "価格チャート",
    },
    "ai signal": {
        "ar": "إشارة الذكاء الاصطناعي", "fr": "Signal IA",
        "es": "Señal IA", "de": "KI-Signal",
        "zh": "AI信号", "ja": "AIシグナル",
    },
    "refresh signal": {
        "ar": "تحديث الإشارة", "fr": "Rafraîchir le signal",
        "es": "Actualizar señal", "de": "Signal aktualisieren",
        "zh": "刷新信号", "ja": "シグナル更新",
    },
    "+ add to journal": {
        "ar": "+ إضافة إلى المذكرة", "fr": "+ Ajouter au journal",
        "es": "+ Agregar al diario", "de": "+ Zum Journal hinzufügen",
        "zh": "+ 添加到日记", "ja": "+ ジャーナルに追加",
    },
    "chart controls": {
        "ar": "أدوات التحكم في الرسم البياني",
        "fr": "Contrôles du graphique",
        "es": "Controles del gráfico",
        "de": "Diagrammsteuerung",
        "zh": "图表控制", "ja": "チャートコントロール",
    },

    "multi-symbol signal scanner": {
        "ar": "ماسح إشارات متعدد الرموز",
        "fr": "Scanner de signaux multi-symboles",
        "es": "Escáner de señales multi-símbolo",
        "de": "Multi-Symbol-Signal-Scanner",
        "zh": "多符号信号扫描器", "ja": "マルチシンボルシグナルスキャナー",
    },
    "scan multiple symbols simultaneously and identify high-confidence setups across your watchlist.": {
        "ar": "امسح رموزاً متعددة في وقت واحد وحدد الإعدادات عالية الثقة عبر قائمة مراقبتك.",
        "fr": "Analysez plusieurs symboles simultanément et identifiez des configurations à haute confiance.",
        "es": "Escanee múltiples símbolos simultáneamente e identifique configuraciones de alta confianza.",
        "de": "Scannen Sie mehrere Symbole gleichzeitig und identifizieren Sie hochzuverlässige Setups.",
        "zh": "同时扫描多个符号，识别高置信度的交易机会。",
        "ja": "複数のシンボルを同時にスキャンし、高信頼度のセットアップを特定します。",
    },
    "scan all": {
        "ar": "مسح الكل", "fr": "Tout scanner", "es": "Escanear todo",
        "de": "Alles scannen", "zh": "全部扫描", "ja": "全スキャン",
    },

    "symbol": {
        "ar": "الرمز", "fr": "Symbole", "es": "Símbolo",
        "de": "Symbol", "zh": "符号", "ja": "シンボル",
    },
    "signal": {
        "ar": "الإشارة", "fr": "Signal", "es": "Señal",
        "de": "Signal", "zh": "信号", "ja": "シグナル",
    },
    "confidence": {
        "ar": "الثقة", "fr": "Confiance", "es": "Confianza",
        "de": "Konfidenz", "zh": "置信度", "ja": "信頼度",
    },
    "entry": {
        "ar": "الدخول", "fr": "Entrée", "es": "Entrada",
        "de": "Einstieg", "zh": "入场", "ja": "エントリー",
    },
    "stop loss": {
        "ar": "وقف الخسارة", "fr": "Stop Loss", "es": "Stop Loss",
        "de": "Stop Loss", "zh": "止损", "ja": "ストップロス",
    },
    "take profit": {
        "ar": "جني الأرباح", "fr": "Prise de profit", "es": "Tomar ganancias",
        "de": "Gewinn mitnehmen", "zh": "止盈", "ja": "テイクプロフィット",
    },
    "r:r": {
        "ar": "المخاطرة:المكافأة", "fr": "R:R", "es": "R:R",
        "de": "R:R", "zh": "风险:回报", "ja": "リスクリワード",
    },
    "pattern": {
        "ar": "النمط", "fr": "Motif", "es": "Patrón",
        "de": "Muster", "zh": "模式", "ja": "パターン",
    },
    "portfolio tracker": {
        "ar": "متتبع المحفظة", "fr": "Suivi de portefeuille",
        "es": "Rastreador de portafolio", "de": "Portfolio-Tracker",
        "zh": "投资组合追踪器", "ja": "ポートフォリオトラッカー",
    },
    "track your open positions, closed trades, and overall performance metrics.": {
        "ar": "تتبع مراكزك المفتوحة والصفقات المغلقة ومقاييس الأداء الإجمالية.",
        "fr": "Suivez vos positions ouvertes, trades fermés et métriques de performance globales.",
        "es": "Realice un seguimiento de sus posiciones abiertas, operaciones cerradas y métricas de rendimiento.",
        "de": "Verfolgen Sie offene Positionen, geschlossene Trades und Gesamtleistungskennzahlen.",
        "zh": "追踪您的开仓、平仓交易和整体业绩指标。",
        "ja": "オープンポジション、クローズトレード、全体的なパフォーマンス指標を追跡します。",
    },
    "add position": {
        "ar": "إضافة مركز", "fr": "Ajouter une position",
        "es": "Agregar posición", "de": "Position hinzufügen",
        "zh": "添加仓位", "ja": "ポジション追加",
    },
    "open positions": {
        "ar": "المراكز المفتوحة", "fr": "Positions ouvertes",
        "es": "Posiciones abiertas", "de": "Offene Positionen",
        "zh": "开仓", "ja": "オープンポジション",
    },
    "closed trades": {
        "ar": "الصفقات المغلقة", "fr": "Trades fermés",
        "es": "Operaciones cerradas", "de": "Geschlossene Trades",
        "zh": "已平仓交易", "ja": "クローズドトレード",
    },
    "close selected": {
        "ar": "إغلاق المحدد", "fr": "Fermer sélectionné",
        "es": "Cerrar seleccionado", "de": "Ausgewähltes schließen",
        "zh": "关闭选中", "ja": "選択を閉じる",
    },
    "refresh prices": {
        "ar": "تحديث الأسعار", "fr": "Actualiser les prix",
        "es": "Actualizar precios", "de": "Preise aktualisieren",
        "zh": "刷新价格", "ja": "価格更新",
    },
    "date": {
        "ar": "التاريخ", "fr": "Date", "es": "Fecha",
        "de": "Datum", "zh": "日期", "ja": "日付",
    },
    "direction": {
        "ar": "الاتجاه", "fr": "Direction", "es": "Dirección",
        "de": "Richtung", "zh": "方向", "ja": "方向",
    },
    "qty": {
        "ar": "الكمية", "fr": "Qté", "es": "Cant.",
        "de": "Menge", "zh": "数量", "ja": "数量",
    },
    "avg cost": {
        "ar": "متوسط التكلفة", "fr": "Coût moy.", "es": "Costo prom.",
        "de": "Durchschn. Kosten", "zh": "平均成本", "ja": "平均コスト",
    },
    "current": {
        "ar": "الحالي", "fr": "Actuel", "es": "Actual",
        "de": "Aktuell", "zh": "当前", "ja": "現在",
    },
    "p&l": {
        "ar": "الربح والخسارة", "fr": "P&L", "es": "P&G",
        "de": "G&V", "zh": "盈亏", "ja": "損益",
    },
    "p&l %": {
        "ar": "نسبة الربح/الخسارة", "fr": "P&L %", "es": "P&G %",
        "de": "G&V %", "zh": "盈亏%", "ja": "損益%",
    },
    "value": {
        "ar": "القيمة", "fr": "Valeur", "es": "Valor",
        "de": "Wert", "zh": "价值", "ja": "価値",
    },
    "exit": {
        "ar": "الخروج", "fr": "Sortie", "es": "Salida",
        "de": "Ausstieg", "zh": "出场", "ja": "エグジット",
    },
    "tags": {
        "ar": "الوسوم", "fr": "Tags", "es": "Etiquetas",
        "de": "Tags", "zh": "标签", "ja": "タグ",
    },

    "trade journal": {
        "ar": "مذكرة التداول", "fr": "Journal de trading",
        "es": "Diario de trading", "de": "Handelsjournal",
        "zh": "交易日记", "ja": "トレードジャーナル",
    },
    "document your trades, thought process, and lessons learned.": {
        "ar": "وثّق صفقاتك وأفكارك والدروس المستفادة.",
        "fr": "Documentez vos trades, votre processus de réflexion et les leçons apprises.",
        "es": "Documente sus operaciones, proceso de pensamiento y lecciones aprendidas.",
        "de": "Dokumentieren Sie Ihre Trades, Denkprozesse und Lektionen.",
        "zh": "记录您的交易、思考过程和经验教训。",
        "ja": "トレード、思考プロセス、学びを記録します。",
    },
    "new journal entry": {
        "ar": "إدخال مذكرة جديد", "fr": "Nouvelle entrée de journal",
        "es": "Nueva entrada de diario", "de": "Neuer Journaleintrag",
        "zh": "新日记条目", "ja": "新しい日記エントリ",
    },
    "save entry": {
        "ar": "حفظ الإدخال", "fr": "Enregistrer l'entrée",
        "es": "Guardar entrada", "de": "Eintrag speichern",
        "zh": "保存条目", "ja": "エントリを保存",
    },
    "notes / reasoning": {
        "ar": "الملاحظات / التفكير", "fr": "Notes / Raisonnement",
        "es": "Notas / Razonamiento", "de": "Notizen / Begründung",
        "zh": "笔记 / 推理", "ja": "メモ / 理由",
    },
    "notes preview": {
        "ar": "معاينة الملاحظات", "fr": "Aperçu des notes",
        "es": "Vista previa de notas", "de": "Notenvorschau",
        "zh": "笔记预览", "ja": "メモプレビュー",
    },

    # ── Risk Calculator ────────────────────────────────────────────────────────
    "inputs": {
        "ar": "المدخلات", "fr": "Entrées", "es": "Entradas",
        "de": "Eingaben", "zh": "输入", "ja": "入力",
    },
    "results": {
        "ar": "النتائج", "fr": "Résultats", "es": "Resultados",
        "de": "Ergebnisse", "zh": "结果", "ja": "結果",
    },
    "calculate": {
        "ar": "احسب", "fr": "Calculer", "es": "Calcular",
        "de": "Berechnen", "zh": "计算", "ja": "計算",
    },
    "account capital ($)": {
        "ar": "رأس المال ($)", "fr": "Capital du compte ($)",
        "es": "Capital de cuenta ($)", "de": "Kontokapital ($)",
        "zh": "账户资金($)", "ja": "口座資本($)",
    },
    "risk per trade (%)": {
        "ar": "المخاطرة لكل صفقة (%)", "fr": "Risque par trade (%)",
        "es": "Riesgo por operación (%)", "de": "Risiko pro Trade (%)",
        "zh": "每笔交易风险(%)", "ja": "取引ごとのリスク(%)",
    },
    "entry price ($)": {
        "ar": "سعر الدخول ($)", "fr": "Prix d'entrée ($)",
        "es": "Precio de entrada ($)", "de": "Einstiegspreis ($)",
        "zh": "入场价格($)", "ja": "エントリー価格($)",
    },
    "stop loss ($)": {
        "ar": "وقف الخسارة ($)", "fr": "Stop Loss ($)",
        "es": "Stop Loss ($)", "de": "Stop Loss ($)",
        "zh": "止损价格($)", "ja": "ストップロス($)",
    },
    "take profit ($)": {
        "ar": "جني الأرباح ($)", "fr": "Prise de profit ($)",
        "es": "Tomar ganancias ($)", "de": "Gewinnziel ($)",
        "zh": "止盈价格($)", "ja": "テイクプロフィット($)",
    },
    "est. win rate (%)": {
        "ar": "معدل الفوز المقدر (%)", "fr": "Taux de réussite est. (%)",
        "es": "Tasa de éxito est. (%)", "de": "Geschätzte Gewinnrate (%)",
        "zh": "估计胜率(%)", "ja": "推定勝率(%)",
    },
    "position size (shares)": {
        "ar": "حجم المركز (أسهم)", "fr": "Taille de position (actions)",
        "es": "Tamaño de posición (acciones)", "de": "Positionsgröße (Aktien)",
        "zh": "仓位大小(股)", "ja": "ポジションサイズ(株)",
    },
    "dollar risk": {
        "ar": "مخاطرة بالدولار", "fr": "Risque en dollars",
        "es": "Riesgo en dólares", "de": "Dollar-Risiko",
        "zh": "美元风险", "ja": "ドルリスク",
    },
    "risk : reward": {
        "ar": "المخاطرة : المكافأة", "fr": "Risque : Récompense",
        "es": "Riesgo : Recompensa", "de": "Risiko : Ertrag",
        "zh": "风险:回报", "ja": "リスク:リワード",
    },
    "expected value": {
        "ar": "القيمة المتوقعة", "fr": "Valeur attendue",
        "es": "Valor esperado", "de": "Erwartungswert",
        "zh": "期望值", "ja": "期待値",
    },
    "breakeven win rate": {
        "ar": "معدل الفوز للتعادل", "fr": "Taux de réussite seuil",
        "es": "Tasa de éxito de equilibrio", "de": "Break-even-Gewinnrate",
        "zh": "盈亏平衡胜率", "ja": "損益分岐勝率",
    },
    "potential profit": {
        "ar": "الربح المحتمل", "fr": "Profit potentiel",
        "es": "Ganancia potencial", "de": "Potenzieller Gewinn",
        "zh": "潜在利润", "ja": "潜在的利益",
    },
    "potential loss": {
        "ar": "الخسارة المحتملة", "fr": "Perte potentielle",
        "es": "Pérdida potencial", "de": "Potenzieller Verlust",
        "zh": "潜在亏损", "ja": "潜在的損失",
    },

    "ai market analyst": {
        "ar": "محلل السوق بالذكاء الاصطناعي",
        "fr": "Analyste de marché IA",
        "es": "Analista de mercado IA",
        "de": "KI-Marktanalyst",
        "zh": "AI市场分析师",
        "ja": "AI市場アナリスト",
    },
    "analyse current signal": {
        "ar": "تحليل الإشارة الحالية", "fr": "Analyser le signal actuel",
        "es": "Analizar señal actual", "de": "Aktuelles Signal analysieren",
        "zh": "分析当前信号", "ja": "現在のシグナルを分析",
    },
    "what are the key risks?": {
        "ar": "ما هي المخاطر الرئيسية؟", "fr": "Quels sont les risques clés ?",
        "es": "¿Cuáles son los riesgos clave?", "de": "Was sind die Hauptrisiken?",
        "zh": "主要风险是什么？", "ja": "主要なリスクは何ですか？",
    },
    "entry/exit strategy": {
        "ar": "استراتيجية الدخول/الخروج",
        "fr": "Stratégie d'entrée/sortie",
        "es": "Estrategia de entrada/salida",
        "de": "Ein-/Ausstiegsstrategie",
        "zh": "进出场策略", "ja": "エントリー/エグジット戦略",
    },
    "market regime": {
        "ar": "نظام السوق", "fr": "Régime de marché",
        "es": "Régimen de mercado", "de": "Marktregime",
        "zh": "市场状态", "ja": "マーケットレジーム",
    },
    "send": {
        "ar": "إرسال", "fr": "Envoyer", "es": "Enviar",
        "de": "Senden", "zh": "发送", "ja": "送信",
    },
    "clear": {
        "ar": "مسح", "fr": "Effacer", "es": "Limpiar",
        "de": "Löschen", "zh": "清除", "ja": "クリア",
    },

    "configure platform behaviour, ai engine, and data settings.": {
        "ar": "تهيئة سلوك المنصة ومحرك الذكاء الاصطناعي وإعدادات البيانات.",
        "fr": "Configurez le comportement de la plateforme, le moteur IA et les paramètres de données.",
        "es": "Configure el comportamiento de la plataforma, el motor de IA y la configuración de datos.",
        "de": "Konfigurieren Sie Plattformverhalten, KI-Engine und Dateneinstellungen.",
        "zh": "配置平台行为、AI引擎和数据设置。",
        "ja": "プラットフォームの動作、AIエンジン、データ設定を構成します。",
    },
    "ai engine": {
        "ar": "محرك الذكاء الاصطناعي", "fr": "Moteur IA",
        "es": "Motor IA", "de": "KI-Engine",
        "zh": "AI引擎", "ja": "AIエンジン",
    },
    "retrain model": {
        "ar": "إعادة تدريب النموذج", "fr": "Réentraîner le modèle",
        "es": "Reentrenar modelo", "de": "Modell neu trainieren",
        "zh": "重新训练模型", "ja": "モデルを再トレーニング",
    },
    "retraining fetches 3 years of daily data for 10 symbols and may take several minutes.": {
        "ar": "يجلب إعادة التدريب بيانات 3 سنوات لـ 10 رموز وقد يستغرق عدة دقائق.",
        "fr": "Le réentraînement récupère 3 ans de données quotidiennes pour 10 symboles et peut prendre plusieurs minutes.",
        "es": "El reentrenamiento obtiene 3 años de datos diarios para 10 símbolos y puede tardar varios minutos.",
        "de": "Das Neutraining ruft 3 Jahre tägliche Daten für 10 Symbole ab und kann mehrere Minuten dauern.",
        "zh": "重新训练将获取10个符号3年的日线数据，可能需要几分钟。",
        "ja": "再トレーニングは10シンボルの3年分の日次データを取得し、数分かかる場合があります。",
    },
    "trading persona": {
        "ar": "شخصية التداول", "fr": "Personnalité de trading",
        "es": "Personalidad de trading", "de": "Handelspersönlichkeit",
        "zh": "交易个性", "ja": "トレードペルソナ",
    },
    "change persona": {
        "ar": "تغيير الشخصية", "fr": "Changer de personnalité",
        "es": "Cambiar personalidad", "de": "Persönlichkeit ändern",
        "zh": "更改个性", "ja": "ペルソナを変更",
    },
    "data & refresh": {
        "ar": "البيانات والتحديث", "fr": "Données et actualisation",
        "es": "Datos y actualización", "de": "Daten & Aktualisierung",
        "zh": "数据与刷新", "ja": "データ＆更新",
    },
    "auto-refresh signal every 30 seconds": {
        "ar": "تحديث الإشارة تلقائياً كل 30 ثانية",
        "fr": "Actualisation automatique du signal toutes les 30 secondes",
        "es": "Actualización automática de señal cada 30 segundos",
        "de": "Signal automatisch alle 30 Sekunden aktualisieren",
        "zh": "每30秒自动刷新信号",
        "ja": "30秒ごとに自動的にシグナルを更新",
    },
    "auto-refresh watchlist prices every 60 seconds": {
        "ar": "تحديث أسعار قائمة المراقبة تلقائياً كل 60 ثانية",
        "fr": "Actualisation automatique des prix de la liste de surveillance toutes les 60 secondes",
        "es": "Actualización automática de precios de la lista de seguimiento cada 60 segundos",
        "de": "Beobachtungslistenpreise automatisch alle 60 Sekunden aktualisieren",
        "zh": "每60秒自动刷新观察列表价格",
        "ja": "60秒ごとにウォッチリスト価格を自動更新",
    },
    "display": {
        "ar": "العرض", "fr": "Affichage", "es": "Pantalla",
        "de": "Anzeige", "zh": "显示", "ja": "ディスプレイ",
    },
    "show ai reasoning text in signal card": {
        "ar": "عرض نص تفكير الذكاء الاصطناعي في بطاقة الإشارة",
        "fr": "Afficher le texte de raisonnement IA dans la carte de signal",
        "es": "Mostrar texto de razonamiento IA en la tarjeta de señal",
        "de": "KI-Begründungstext in der Signalkarte anzeigen",
        "zh": "在信号卡中显示AI推理文本",
        "ja": "シグナルカードにAI推論テキストを表示",
    },
    "about red rook": {
        "ar": "حول الرخ الأحمر", "fr": "À propos de Tour Rouge",
        "es": "Acerca de Torre Roja", "de": "Über Roter Turm",
        "zh": "关于红车", "ja": "レッドルークについて",
    },

    "ready  ·  red rook trading platform": {
        "ar": "جاهز · منصة الرخ الأحمر للتداول",
        "fr": "Prêt · Plateforme de Trading Tour Rouge",
        "es": "Listo · Plataforma de Trading Torre Roja",
        "de": "Bereit · Roter Turm Handelsplattform",
        "zh": "就绪 · 红车交易平台",
        "ja": "準備完了 · レッドルーク取引プラットフォーム",
    },
    "live": {
        "ar": "مباشر", "fr": "En direct", "es": "En vivo",
        "de": "Live", "zh": "实时", "ja": "ライブ",
    },

    "ask the ai analyst anything…": {
        "ar": "اسأل محلل الذكاء الاصطناعي أي شيء…",
        "fr": "Demandez n'importe quoi à l'analyste IA…",
        "es": "Pregúntele cualquier cosa al analista IA…",
        "de": "Fragen Sie den KI-Analysten alles…",
        "zh": "询问AI分析师任何问题…",
        "ja": "AIアナリストに何でも聞いてください…",
    },
    "risk summary will appear here after calculation…": {
        "ar": "ستظهر ملخص المخاطر هنا بعد الحساب…",
        "fr": "Le résumé du risque apparaîtra ici après le calcul…",
        "es": "El resumen de riesgo aparecerá aquí después del cálculo…",
        "de": "Die Risikoübersicht erscheint hier nach der Berechnung…",
        "zh": "计算后风险摘要将显示在此处…",
        "ja": "計算後にリスクサマリーがここに表示されます…",
    },
    "describe your trade setup, entry reasoning, and any lessons learned...": {
        "ar": "صف إعداد صفقتك ومنطق الدخول وأي دروس مستفادة...",
        "fr": "Décrivez votre configuration de trade, le raisonnement d'entrée et les leçons apprises...",
        "es": "Describa su configuración de operación, razonamiento de entrada y lecciones aprendidas...",
        "de": "Beschreiben Sie Ihr Trade-Setup, Einstiegsbegründung und Lektionen...",
        "zh": "描述您的交易设置、入场理由和经验教训...",
        "ja": "トレードのセットアップ、エントリー理由、学びを記述してください...",
    },

    "language": {
        "ar": "اللغة", "fr": "Langue", "es": "Idioma",
        "de": "Sprache", "zh": "语言", "ja": "言語",
    },
}

_LOOKUP: Dict[str, Dict[str, str]] = {k.lower().strip(): v for k, v in _T.items()}


def tr(text: str, lang: str) -> str:
    """Return translated text, or original if no translation found."""
    if lang == "en" or not text:
        return text
    key = text.lower().strip()
    translations = _LOOKUP.get(key)
    if translations:
        return translations.get(lang, text)
    return text


def _translate_widget(widget: QWidget, lang: str):
    """Recursively translate a single widget and all its children."""

    if isinstance(widget, QLabel):
        t = tr(widget.text(), lang)
        if t != widget.text():
            widget.setText(t)

    elif isinstance(widget, (QPushButton, QCheckBox)):
        t = tr(widget.text(), lang)
        if t != widget.text():
            widget.setText(t)

    elif isinstance(widget, QGroupBox):
        t = tr(widget.title(), lang)
        if t != widget.title():
            widget.setTitle(t)

    if isinstance(widget, QLineEdit):
        t = tr(widget.placeholderText(), lang)
        if t != widget.placeholderText():
            widget.setPlaceholderText(t)

    if isinstance(widget, QTextEdit):
        t = tr(widget.placeholderText(), lang)
        if t != widget.placeholderText():
            widget.setPlaceholderText(t)

    if isinstance(widget, QTableWidget):
        hh = widget.horizontalHeader()
        model = hh.model()
        if model:
            for col in range(widget.columnCount()):
                orig = model.headerData(col, Qt.Horizontal, Qt.DisplayRole)
                if orig:
                    t = tr(str(orig), lang)
                    if t != str(orig):
                        model.setHeaderData(col, Qt.Horizontal, t, Qt.DisplayRole)

    if isinstance(widget, QTabWidget):
        for i in range(widget.count()):
            orig = widget.tabText(i)
            t = tr(orig, lang)
            if t != orig:
                widget.setTabText(i, t)

    if isinstance(widget, QMainWindow):
        t = tr(widget.windowTitle(), lang)
        if t != widget.windowTitle():
            widget.setWindowTitle(t)

    for child in widget.findChildren(QWidget):
        pass

    for child in widget.children():
        if isinstance(child, QWidget):
            _translate_widget(child, lang)


def translate_app(lang: str):
    """Translate every widget in the entire running application."""
    app = QApplication.instance()
    if not app:
        return

    if lang in RTL_LANGS:
        app.setLayoutDirection(Qt.RightToLeft)
    else:
        app.setLayoutDirection(Qt.LeftToRight)

    for top in app.topLevelWidgets():
        _translate_widget(top, lang)
        if hasattr(top, "windowTitle"):
            t = tr(top.windowTitle(), lang)
            if t != top.windowTitle():
                top.setWindowTitle(t)

class LanguageSwitcher(QObject):
    language_changed = pyqtSignal(str)

    def __init__(self, main_window: QMainWindow, default_lang: str = "en"):
        super().__init__(main_window)
        self._window = main_window
        self._lang = default_lang
        self._toolbar = self._build_toolbar()
        main_window.addToolBar(Qt.TopToolBarArea, self._toolbar)

    def _build_toolbar(self) -> QToolBar:
        tb = QToolBar("Language", self._window)
        tb.setMovable(False)
        tb.setFloatable(False)
        tb.setStyleSheet(
            "QToolBar { background: #141414; border-bottom: 1px solid #222; spacing: 6px; padding: 2px 8px; }"
            "QLabel   { color: #6a6a6a; font-family: 'Courier New'; font-size: 10px; }"
            "QComboBox { background: #1a1a1a; color: #f0f0f0; border: 1px solid #222; "
            "            font-family: 'Courier New'; font-size: 10px; padding: 2px 6px; min-width: 120px; }"
            "QComboBox::drop-down { border: none; width: 18px; }"
            "QComboBox QAbstractItemView { background: #1a1a1a; color: #f0f0f0; selection-background-color: #941107; }"
        )

        lbl = QLabel("Language / اللغة / Langue :  ")
        tb.addWidget(lbl)

        combo = QComboBox()
        for code, name in LANGUAGES.items():
            combo.addItem(f"{name}  [{code}]", code)

        # Set default
        for i in range(combo.count()):
            if combo.itemData(i) == self._lang:
                combo.setCurrentIndex(i)
                break

        combo.currentIndexChanged.connect(self._on_lang_changed)
        tb.addWidget(combo)
        self._combo = combo

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tb.addWidget(spacer)

        return tb

    def _on_lang_changed(self, _index: int):
        lang = self._combo.currentData()
        if lang == self._lang:
            return
        self._lang = lang
        QTimer.singleShot(50, lambda: translate_app(lang))
        self.language_changed.emit(lang)

    @property
    def current_lang(self) -> str:
        return self._lang

_switcher: Optional[LanguageSwitcher] = None


def install_translator(app: QApplication, default_lang: str = "en") -> LanguageSwitcher:
    """
    Install the translator into the given QApplication instance.
    This will inject a language switcher toolbar into the main window and translate all widgets.
    """
    global _switcher

    main_win: Optional[QMainWindow] = None
    for w in app.topLevelWidgets():
        if isinstance(w, QMainWindow):
            main_win = w
            break

    if main_win is None:
        def _retry():
            install_translator(app, default_lang)
        QTimer.singleShot(500, _retry)
        return None  # type: ignore

    _switcher = LanguageSwitcher(main_win, default_lang)

    if default_lang != "en":
        QTimer.singleShot(200, lambda: translate_app(default_lang))

    return _switcher