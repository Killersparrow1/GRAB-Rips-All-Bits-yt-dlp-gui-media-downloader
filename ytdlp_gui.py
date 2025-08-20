#!/usr/bin/env python3

import os
import subprocess
import json
import threading
import time
import tempfile
import shutil
from datetime import datetime
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf, WebKit2

class GRABApp:
    def __init__(self):
        # Create main window
        self.window = Gtk.Window(title="GRAB - Rips All Bits")
        self.window.set_default_size(1000, 800)
        
        # Create a scrolled window for the main content
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.window.add(scrolled_window)
        
        # Load settings
        self.load_settings()
        
        # Apply theme based on settings
        settings = Gtk.Settings.get_default()
        settings.set_property("gtk-application-prefer-dark-theme", self.use_dark_theme)
        
        # Main container with margin
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_top(10)
        main_box.set_margin_bottom(10)
        main_box.set_margin_start(10)
        main_box.set_margin_end(10)
        scrolled_window.add(main_box)
        
        # Header with logo and theme toggle
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        main_box.pack_start(header_box, False, False, 0)
        
        try:
            # Create a simple logo programmatically
            logo = Gtk.Image.new_from_icon_name("video-x-generic", Gtk.IconSize.DIALOG)
        except:
            # Fallback if icon not found
            logo = Gtk.Label(label="🎬")
        
        header_box.pack_start(logo, False, False, 0)
        
        title = Gtk.Label()
        title.set_markup("<span size='xx-large' weight='bold'>GRAB - Rips All Bits</span>")
        header_box.pack_start(title, False, False, 0)
        
        # Theme toggle button
        self.theme_button = Gtk.Button(label="🌙" if self.use_dark_theme else "☀️")
        self.theme_button.connect("clicked", self.on_toggle_theme)
        header_box.pack_end(self.theme_button, False, False, 0)
        
        # Incognito button
        incognito_button = Gtk.Button(label="Incognito")
        incognito_button.connect("clicked", self.on_incognito_mode)
        header_box.pack_end(incognito_button, False, False, 0)
        
        # Clear cache button
        clear_cache_button = Gtk.Button(label="Clear Cache")
        clear_cache_button.connect("clicked", self.on_clear_cache)
        header_box.pack_end(clear_cache_button, False, False, 0)
        
        # Create notebook for tabs
        self.notebook = Gtk.Notebook()
        main_box.pack_start(self.notebook, True, True, 0)
        
        # Download tab with scroll
        download_scrolled = Gtk.ScrolledWindow()
        download_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.notebook.append_page(download_scrolled, Gtk.Label(label="Download"))
        
        download_tab = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        download_tab.set_margin_top(5)
        download_tab.set_margin_bottom(5)
        download_tab.set_margin_start(5)
        download_tab.set_margin_end(5)
        download_scrolled.add(download_tab)
        
        # Cookie tab with scroll
        cookie_scrolled = Gtk.ScrolledWindow()
        cookie_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.notebook.append_page(cookie_scrolled, Gtk.Label(label="Cookie Extraction"))
        
        cookie_tab = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        cookie_tab.set_margin_top(5)
        cookie_tab.set_margin_bottom(5)
        cookie_tab.set_margin_start(5)
        cookie_tab.set_margin_end(5)
        cookie_scrolled.add(cookie_tab)
        
        # Settings tab with scroll
        settings_scrolled = Gtk.ScrolledWindow()
        settings_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.notebook.append_page(settings_scrolled, Gtk.Label(label="Settings"))
        
        settings_tab = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        settings_tab.set_margin_top(5)
        settings_tab.set_margin_bottom(5)
        settings_tab.set_margin_start(5)
        settings_tab.set_margin_end(5)
        settings_scrolled.add(settings_tab)
        
        # URL entry
        url_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        download_tab.pack_start(url_box, False, False, 0)
        
        url_label = Gtk.Label(label="Video URL:")
        url_box.pack_start(url_label, False, False, 0)
        
        self.url_entry = Gtk.Entry()
        self.url_entry.set_placeholder_text("Enter video or playlist URL here")
        self.url_entry.set_hexpand(True)
        url_box.pack_start(self.url_entry, True, True, 0)
        
        # Media type selection
        media_type_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        download_tab.pack_start(media_type_box, False, False, 0)
        
        media_type_label = Gtk.Label(label="Media Type:")
        media_type_box.pack_start(media_type_label, False, False, 0)
        
        self.media_type_combo = Gtk.ComboBoxText()
        self.media_type_combo.append_text("Video")
        self.media_type_combo.append_text("Audio")
        self.media_type_combo.set_active(0)
        media_type_box.pack_start(self.media_type_combo, True, True, 0)
        
        # History dropdown
        history_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        download_tab.pack_start(history_box, False, False, 0)
        
        history_label = Gtk.Label(label="History:")
        history_box.pack_start(history_label, False, False, 0)
        
        self.history_combo = Gtk.ComboBoxText()
        self.history_combo.set_hexpand(True)
        history_box.pack_start(self.history_combo, True, True, 0)
        
        # Load history
        self.load_history()
        self.history_combo.connect("changed", self.on_history_selected)
        
        # Cookie options
        cookie_frame = Gtk.Frame(label="Cookie Options")
        download_tab.pack_start(cookie_frame, False, False, 0)
        
        cookie_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        cookie_box.set_margin_top(5)
        cookie_box.set_margin_bottom(5)
        cookie_box.set_margin_start(5)
        cookie_box.set_margin_end(5)
        cookie_frame.add(cookie_box)
        
        cookie_file_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        cookie_box.pack_start(cookie_file_box, False, False, 0)
        
        cookie_label = Gtk.Label(label="Cookie File:")
        cookie_file_box.pack_start(cookie_label, False, False, 0)
        
        self.cookie_entry = Gtk.Entry()
        self.cookie_entry.set_placeholder_text("Path to cookie file (optional)")
        self.cookie_entry.set_hexpand(True)
        cookie_file_box.pack_start(self.cookie_entry, True, True, 0)
        
        cookie_button = Gtk.Button(label="Browse")
        cookie_button.connect("clicked", self.on_browse_cookie)
        cookie_file_box.pack_start(cookie_button, False, False, 0)
        
        # Saved cookies dropdown
        saved_cookie_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        cookie_box.pack_start(saved_cookie_box, False, False, 0)
        
        saved_cookie_label = Gtk.Label(label="Saved Cookies:")
        saved_cookie_box.pack_start(saved_cookie_label, False, False, 0)
        
        self.saved_cookie_combo = Gtk.ComboBoxText()
        self.saved_cookie_combo.set_hexpand(True)
        saved_cookie_box.pack_start(self.saved_cookie_combo, True, True, 0)
        
        use_cookie_button = Gtk.Button(label="Use Selected")
        use_cookie_button.connect("clicked", self.on_use_saved_cookie)
        saved_cookie_box.pack_start(use_cookie_button, False, False, 0)
        
        # Load saved cookies
        self.load_saved_cookies()
        
        # Quality options
        quality_frame = Gtk.Frame(label="Quality Options")
        download_tab.pack_start(quality_frame, False, False, 0)
        
        quality_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        quality_box.set_margin_top(5)
        quality_box.set_margin_bottom(5)
        quality_box.set_margin_start(5)
        quality_box.set_margin_end(5)
        quality_frame.add(quality_box)
        
        quality_select_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        quality_box.pack_start(quality_select_box, False, False, 0)
        
        quality_label = Gtk.Label(label="Select Quality:")
        quality_select_box.pack_start(quality_label, False, False, 0)
        
        self.quality_combo = Gtk.ComboBoxText()
        self.quality_combo.set_hexpand(True)
        quality_select_box.pack_start(self.quality_combo, True, True, 0)
        
        fetch_button = Gtk.Button(label="Fetch Available Qualities")
        fetch_button.connect("clicked", self.on_fetch_qualities)
        quality_select_box.pack_start(fetch_button, False, False, 0)
        
        # Format options
        format_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        quality_box.pack_start(format_box, False, False, 0)
        
        format_label = Gtk.Label(label="Format:")
        format_box.pack_start(format_label, False, False, 0)
        
        self.format_combo = Gtk.ComboBoxText()
        self.format_combo.append_text("mp4")
        self.format_combo.append_text("mkv")
        self.format_combo.append_text("webm")
        self.format_combo.append_text("mp3")
        self.format_combo.append_text("m4a")
        self.format_combo.append_text("flac")
        self.format_combo.append_text("best")
        self.format_combo.set_active(6)  # Default to "best"
        format_box.pack_start(self.format_combo, True, True, 0)
        
        # SponsorBlock options
        sponsor_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        quality_box.pack_start(sponsor_box, False, False, 0)
        
        sponsor_label = Gtk.Label(label="SponsorBlock:")
        sponsor_box.pack_start(sponsor_label, False, False, 0)
        
        self.sponsor_combo = Gtk.ComboBoxText()
        self.sponsor_combo.append_text("None")
        self.sponsor_combo.append_text("Remove all sponsors")
        self.sponsor_combo.append_text("Remove sponsors, intros, outros")
        self.sponsor_combo.append_text("Remove all possible segments")
        self.sponsor_combo.set_active(0)
        sponsor_box.pack_start(self.sponsor_combo, True, True, 0)
        
        # Metadata options
        metadata_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        quality_box.pack_start(metadata_box, False, False, 0)
        
        self.embed_metadata = Gtk.CheckButton(label="Embed metadata")
        self.embed_metadata.set_active(True)
        metadata_box.pack_start(self.embed_metadata, False, False, 0)
        
        self.embed_thumbnail = Gtk.CheckButton(label="Embed thumbnail")
        self.embed_thumbnail.set_active(True)
        metadata_box.pack_start(self.embed_thumbnail, False, False, 0)
        
        # Output path
        output_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        download_tab.pack_start(output_box, False, False, 0)
        
        output_label = Gtk.Label(label="Download Folder:")
        output_box.pack_start(output_label, False, False, 0)
        
        self.output_entry = Gtk.Entry()
        self.output_entry.set_text(os.path.expanduser("~/Downloads"))
        self.output_entry.set_hexpand(True)
        output_box.pack_start(self.output_entry, True, True, 0)
        
        output_button = Gtk.Button(label="Browse")
        output_button.connect("clicked", self.on_browse_output)
        output_box.pack_start(output_button, False, False, 0)
        
        # Media info box
        self.media_info_frame = Gtk.Frame(label="Media Information")
        download_tab.pack_start(self.media_info_frame, False, False, 0)
        
        media_info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        media_info_box.set_margin_top(5)
        media_info_box.set_margin_bottom(5)
        media_info_box.set_margin_start(5)
        media_info_box.set_margin_end(5)
        self.media_info_frame.add(media_info_box)
        
        self.media_title = Gtk.Label(label="Title: Not loaded")
        media_info_box.pack_start(self.media_title, False, False, 0)
        
        self.media_duration = Gtk.Label(label="Duration: Not loaded")
        media_info_box.pack_start(self.media_duration, False, False, 0)
        
        self.media_thumbnail = Gtk.Image()
        media_info_box.pack_start(self.media_thumbnail, False, False, 0)
        
        # Initially hide media info
        self.media_info_frame.hide()
        
        # Progress bar
        self.progress_bar = Gtk.ProgressBar()
        download_tab.pack_start(self.progress_bar, False, False, 0)
        
        # Status label
        self.status_label = Gtk.Label(label="Ready")
        download_tab.pack_start(self.status_label, False, False, 0)
        
        # Download queue
        queue_frame = Gtk.Frame(label="Download Queue")
        download_tab.pack_start(queue_frame, True, True, 0)
        
        queue_scrolled = Gtk.ScrolledWindow()
        queue_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        queue_scrolled.set_min_content_height(100)
        queue_frame.add(queue_scrolled)
        
        self.queue_list = Gtk.ListStore(str, str, str)  # URL, status, progress
        self.queue_treeview = Gtk.TreeView(model=self.queue_list)
        
        # URL column
        url_renderer = Gtk.CellRendererText()
        url_column = Gtk.TreeViewColumn("URL", url_renderer, text=0)
        url_column.set_expand(True)
        self.queue_treeview.append_column(url_column)
        
        # Status column
        status_renderer = Gtk.CellRendererText()
        status_column = Gtk.TreeViewColumn("Status", status_renderer, text=1)
        self.queue_treeview.append_column(status_column)
        
        # Progress column
        progress_renderer = Gtk.CellRendererText()
        progress_column = Gtk.TreeViewColumn("Progress", progress_renderer, text=2)
        self.queue_treeview.append_column(progress_column)
        
        queue_scrolled.add(self.queue_treeview)
        
        # Log view
        log_frame = Gtk.Frame(label="Download Log")
        download_tab.pack_start(log_frame, True, True, 0)
        
        log_scrolled = Gtk.ScrolledWindow()
        log_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        log_scrolled.set_min_content_height(100)
        log_frame.add(log_scrolled)
        
        self.log_view = Gtk.TextView()
        self.log_view.set_editable(False)
        self.log_view.set_wrap_mode(Gtk.WrapMode.WORD)
        log_scrolled.add(self.log_view)
        
        # Buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        download_tab.pack_start(button_box, False, False, 0)
        
        self.download_button = Gtk.Button(label="Download")
        self.download_button.connect("clicked", self.on_download)
        button_box.pack_start(self.download_button, True, True, 0)
        
        queue_button = Gtk.Button(label="Add to Queue")
        queue_button.connect("clicked", self.on_add_to_queue)
        button_box.pack_start(queue_button, True, True, 0)
        
        self.pause_button = Gtk.Button(label="Pause")
        self.pause_button.connect("clicked", self.on_pause)
        self.pause_button.set_sensitive(False)
        button_box.pack_start(self.pause_button, True, True, 0)
        
        self.stop_button = Gtk.Button(label="Stop")
        self.stop_button.connect("clicked", self.on_stop)
        self.stop_button.set_sensitive(False)
        button_box.pack_start(self.stop_button, True, True, 0)
        
        # Error reporting button
        report_button = Gtk.Button(label="Report Error to yt-dlp")
        report_button.connect("clicked", self.on_report_error)
        button_box.pack_start(report_button, True, True, 0)
        
        # Cookie extraction tab content
        cookie_extraction_label = Gtk.Label()
        cookie_extraction_label.set_markup("<b>Cookie Extraction</b>\n\nEnter a URL to open in the built-in browser. Login to the website, then extract the cookies.")
        cookie_extraction_label.set_line_wrap(True)
        cookie_tab.pack_start(cookie_extraction_label, False, False, 0)
        
        # URL entry for cookie extraction
        cookie_url_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        cookie_tab.pack_start(cookie_url_box, False, False, 0)
        
        cookie_url_label = Gtk.Label(label="Website URL:")
        cookie_url_box.pack_start(cookie_url_label, False, False, 0)
        
        self.cookie_url_entry = Gtk.Entry()
        self.cookie_url_entry.set_placeholder_text("https://example.com")
        self.cookie_url_entry.set_hexpand(True)
        cookie_url_box.pack_start(self.cookie_url_entry, True, True, 0)
        
        open_browser_button = Gtk.Button(label="Open Browser")
        open_browser_button.connect("clicked", self.on_open_browser)
        cookie_url_box.pack_start(open_browser_button, False, False, 0)
        
        # Web view for cookie extraction
        web_frame = Gtk.Frame(label="Browser")
        cookie_tab.pack_start(web_frame, True, True, 0)
        
        web_scrolled = Gtk.ScrolledWindow()
        web_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        web_frame.add(web_scrolled)
        
        self.web_view = WebKit2.WebView()
        web_scrolled.add(self.web_view)
        
        # Cookie extraction buttons
        cookie_extract_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        cookie_tab.pack_start(cookie_extract_box, False, False, 0)
        
        extract_button = Gtk.Button(label="Extract Cookies")
        extract_button.connect("clicked", self.on_extract_cookies)
        cookie_extract_box.pack_start(extract_button, True, True, 0)
        
        save_cookie_button = Gtk.Button(label="Save Cookies")
        save_cookie_button.connect("clicked", self.on_save_cookies)
        cookie_extract_box.pack_start(save_cookie_button, True, True, 0)
        
        # Settings tab content
        settings_label = Gtk.Label()
        settings_label.set_markup("<b>Application Settings</b>")
        settings_tab.pack_start(settings_label, False, False, 0)
        
        # Theme settings
        theme_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        settings_tab.pack_start(theme_box, False, False, 0)
        
        theme_label = Gtk.Label(label="Theme:")
        theme_box.pack_start(theme_label, False, False, 0)
        
        self.theme_combo = Gtk.ComboBoxText()
        self.theme_combo.append_text("Follow System")
        self.theme_combo.append_text("Light")
        self.theme_combo.append_text("Dark")
        self.theme_combo.set_active(0 if self.theme_follows_system else (2 if self.use_dark_theme else 1))
        self.theme_combo.connect("changed", self.on_theme_changed)
        theme_box.pack_start(self.theme_combo, True, True, 0)
        
        # Default download options
        defaults_frame = Gtk.Frame(label="Default Download Options")
        settings_tab.pack_start(defaults_frame, False, False, 0)
        
        defaults_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        defaults_box.set_margin_top(5)
        defaults_box.set_margin_bottom(5)
        defaults_box.set_margin_start(5)
        defaults_box.set_margin_end(5)
        defaults_frame.add(defaults_box)
        
        # Default format
        format_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        defaults_box.pack_start(format_box, False, False, 0)
        
        format_label = Gtk.Label(label="Default Format:")
        format_box.pack_start(format_label, False, False, 0)
        
        self.default_format_combo = Gtk.ComboBoxText()
        self.default_format_combo.append_text("mp4")
        self.default_format_combo.append_text("mkv")
        self.default_format_combo.append_text("webm")
        self.default_format_combo.append_text("mp3")
        self.default_format_combo.append_text("m4a")
        self.default_format_combo.append_text("flac")
        self.default_format_combo.append_text("best")
        self.default_format_combo.set_active(self.default_format)
        format_box.pack_start(self.default_format_combo, True, True, 0)
        
        # Default media type
        media_type_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        defaults_box.pack_start(media_type_box, False, False, 0)
        
        media_type_label = Gtk.Label(label="Default Media Type:")
        media_type_box.pack_start(media_type_label, False, False, 0)
        
        self.default_media_type_combo = Gtk.ComboBoxText()
        self.default_media_type_combo.append_text("Video")
        self.default_media_type_combo.append_text("Audio")
        self.default_media_type_combo.set_active(self.default_media_type)
        media_type_box.pack_start(self.default_media_type_combo, True, True, 0)
        
        # Default output path
        output_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        defaults_box.pack_start(output_box, False, False, 0)
        
        output_label = Gtk.Label(label="Default Download Path:")
        output_box.pack_start(output_label, False, False, 0)
        
        self.default_output_entry = Gtk.Entry()
        self.default_output_entry.set_text(self.default_output_path)
        self.default_output_entry.set_hexpand(True)
        output_box.pack_start(self.default_output_entry, True, True, 0)
        
        output_button = Gtk.Button(label="Browse")
        output_button.connect("clicked", self.on_browse_default_output)
        output_box.pack_start(output_button, False, False, 0)
        
        # Settings buttons
        settings_buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        settings_tab.pack_start(settings_buttons_box, False, False, 0)
        
        save_settings_button = Gtk.Button(label="Save Settings")
        save_settings_button.connect("clicked", self.on_save_settings)
        settings_buttons_box.pack_start(save_settings_button, True, True, 0)
        
        backup_button = Gtk.Button(label="Backup Settings")
        backup_button.connect("clicked", self.on_backup_settings)
        settings_buttons_box.pack_start(backup_button, True, True, 0)
        
        restore_button = Gtk.Button(label="Restore Settings")
        restore_button.connect("clicked", self.on_restore_settings)
        settings_buttons_box.pack_start(restore_button, True, True, 0)
        
        # Initialize variables
        self.downloading = False
        self.paused = False
        self.process = None
        self.temp_cookie_file = None
        self.cookie_manager = self.web_view.get_website_data_manager().get_cookie_manager()
        self.current_download_name = ""
        self.download_queue = []
        self.current_download_index = -1
        self.incognito_mode = False
        
        # Connect signals
        self.window.connect("destroy", self.on_destroy)
        
        # Show all
        self.window.show_all()
    
    def load_settings(self):
        """Load application settings"""
        self.settings_file = os.path.expanduser("~/.grab_settings.json")
        default_settings = {
            "use_dark_theme": True,
            "theme_follows_system": True,
            "default_format": 6,  # best
            "default_media_type": 0,  # Video
            "default_output_path": os.path.expanduser("~/Downloads"),
            "sponsorblock": 0,  # None
            "embed_metadata": True,
            "embed_thumbnail": True
        }
        
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    # Merge with default settings in case new options were added
                    for key, value in default_settings.items():
                        if key not in settings:
                            settings[key] = value
            except:
                settings = default_settings
        else:
            settings = default_settings
        
        # Apply settings
        self.use_dark_theme = settings["use_dark_theme"]
        self.theme_follows_system = settings["theme_follows_system"]
        self.default_format = settings["default_format"]
        self.default_media_type = settings["default_media_type"]
        self.default_output_path = settings["default_output_path"]
        self.default_sponsorblock = settings["sponsorblock"]
        self.default_embed_metadata = settings["embed_metadata"]
        self.default_embed_thumbnail = settings["embed_thumbnail"]
        
        # Apply system theme detection if needed
        if self.theme_follows_system:
            try:
                # Try to detect system dark mode (this is a simple approach)
                output = subprocess.check_output(["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"]).decode().strip()
                self.use_dark_theme = "dark" in output.lower()
            except:
                # Fallback to dark theme if detection fails
                self.use_dark_theme = True
    
    def save_settings(self):
        """Save application settings"""
        settings = {
            "use_dark_theme": self.use_dark_theme,
            "theme_follows_system": self.theme_follows_system,
            "default_format": self.default_format,
            "default_media_type": self.default_media_type,
            "default_output_path": self.default_output_path,
            "sponsorblock": self.default_sponsorblock,
            "embed_metadata": self.default_embed_metadata,
            "embed_thumbnail": self.default_embed_thumbnail
        }
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
        
        with open(self.settings_file, 'w') as f:
            json.dump(settings, f, indent=4)
    
    def load_history(self):
        """Load download history from file"""
        self.history = []
        history_file = os.path.expanduser("~/.grab_history")
        
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r') as f:
                    self.history = [line.strip() for line in f.readlines() if line.strip()]
            except:
                self.history = []
        
        self.history_combo.remove_all()
        for item in self.history:
            self.history_combo.append_text(item)
            
    def save_history(self, url):
        """Save URL to history file"""
        if self.incognito_mode:
            return
            
        if url in self.history:
            self.history.remove(url)
        
        self.history.insert(0, url)
        if len(self.history) > 20:  # Keep only 20 most recent
            self.history = self.history[:20]
        
        history_file = os.path.expanduser("~/.grab_history")
        try:
            with open(history_file, 'w') as f:
                for item in self.history:
                    f.write(item + "\n")
        except:
            pass
        
        # Update combo box
        self.history_combo.remove_all()
        for item in self.history:
            self.history_combo.append_text(item)
    
    def load_saved_cookies(self):
        """Load saved cookies from app data directory"""
        self.saved_cookies = {}
        cookie_dir = os.path.expanduser("~/.grab/cookies")
        
        if not os.path.exists(cookie_dir):
            os.makedirs(cookie_dir, exist_ok=True)
            return
        
        try:
            for file in os.listdir(cookie_dir):
                if file.endswith('.txt'):
                    cookie_name = file[:-4]  # Remove .txt extension
                    self.saved_cookies[cookie_name] = os.path.join(cookie_dir, file)
        except:
            pass
        
        # Update combo box
        self.saved_cookie_combo.remove_all()
        for cookie_name in self.saved_cookies:
            self.saved_cookie_combo.append_text(cookie_name)
    
    def on_history_selected(self, combo):
        """When a history item is selected"""
        active_id = combo.get_active()
        if active_id >= 0 and active_id < len(self.history):
            self.url_entry.set_text(self.history[active_id])
            # Auto-fetch media info when selecting from history
            self.fetch_media_info()
    
    def on_use_saved_cookie(self, widget):
        """Use a saved cookie file"""
        active_id = self.saved_cookie_combo.get_active()
        if active_id >= 0:
            cookie_name = self.saved_cookie_combo.get_active_text()
            if cookie_name in self.saved_cookies:
                self.cookie_entry.set_text(self.saved_cookies[cookie_name])
    
    def on_browse_cookie(self, widget):
        """Open file chooser for cookie file"""
        dialog = Gtk.FileChooserDialog(
            title="Select Cookie File",
            parent=self.window,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        # Add filters for text files
        filter_text = Gtk.FileFilter()
        filter_text.set_name("Text files")
        filter_text.add_mime_type("text/plain")
        dialog.add_filter(filter_text)
        
        filter_any = Gtk.FileFilter()
        filter_any.set_name("Any files")
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.cookie_entry.set_text(dialog.get_filename())
        
        dialog.destroy()
    
    def on_browse_output(self, widget):
        """Open file chooser for output directory"""
        dialog = Gtk.FileChooserDialog(
            title="Select Download Directory",
            parent=self.window,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.output_entry.set_text(dialog.get_filename())
        
        dialog.destroy()
    
    def on_browse_default_output(self, widget):
        """Open file chooser for default output directory"""
        dialog = Gtk.FileChooserDialog(
            title="Select Default Download Directory",
            parent=self.window,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.default_output_entry.set_text(dialog.get_filename())
        
        dialog.destroy()
    
    def on_toggle_theme(self, widget):
        """Toggle between light and dark theme"""
        self.use_dark_theme = not self.use_dark_theme
        self.theme_follows_system = False
        
        settings = Gtk.Settings.get_default()
        settings.set_property("gtk-application-prefer-dark-theme", self.use_dark_theme)
        
        self.theme_button.set_label("🌙" if self.use_dark_theme else "☀️")
        self.theme_combo.set_active(2 if self.use_dark_theme else 1)
        self.save_settings()
    
    def on_theme_changed(self, widget):
        """Handle theme selection change"""
        selected = widget.get_active_text()
        if selected == "Follow System":
            self.theme_follows_system = True
            try:
                output = subprocess.check_output(["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"]).decode().strip()
                self.use_dark_theme = "dark" in output.lower()
            except:
                self.use_dark_theme = True
        elif selected == "Light":
            self.theme_follows_system = False
            self.use_dark_theme = False
        else:  # Dark
            self.theme_follows_system = False
            self.use_dark_theme = True
        
        settings = Gtk.Settings.get_default()
        settings.set_property("gtk-application-prefer-dark-theme", self.use_dark_theme)
        self.theme_button.set_label("🌙" if self.use_dark_theme else "☀️")
        self.save_settings()
    
    def on_incognito_mode(self, widget):
        """Toggle incognito mode"""
        self.incognito_mode = not self.incognito_mode
        if self.incognito_mode:
            widget.set_label("Incognito ✓")
            self.show_info("Incognito mode enabled - history won't be saved")
        else:
            widget.set_label("Incognito")
            self.show_info("Incognito mode disabled")
    
    def on_clear_cache(self, widget):
        """Clear application cache"""
        dialog = Gtk.MessageDialog(
            parent=self.window,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Clear Cache"
        )
        dialog.format_secondary_text("Are you sure you want to clear all cache? This will remove temporary files but keep your settings and history.")
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            # Clear temporary files
            temp_dir = tempfile.gettempdir()
            for file in os.listdir(temp_dir):
                if file.startswith("grab_"):
                    try:
                        os.remove(os.path.join(temp_dir, file))
                    except:
                        pass
            
            # Clear web data
            try:
                self.web_view.get_website_data_manager().clear(
                    WebKit2.WebsiteDataTypes.ALL,
                    time.time() - 3600,  # Last hour
                    None, None, None
                )
            except:
                pass
            
            self.show_info("Cache cleared successfully")
    
    def fetch_media_info(self):
        """Fetch media information for the current URL"""
        url = self.url_entry.get_text().strip()
        if not url:
            return
        
        # Run in thread to avoid blocking UI
        thread = threading.Thread(target=self.fetch_media_info_thread, args=(url,))
        thread.daemon = True
        thread.start()
    
    def fetch_media_info_thread(self, url):
        """Thread function to fetch media information"""
        cookie_file = self.cookie_entry.get_text().strip()
        cmd = [
            'yt-dlp', 
            '--dump-json',
            '--no-warnings',
            url
        ]
        
        if cookie_file:
            cmd.extend(['--cookies', cookie_file])
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                GLib.idle_add(self.show_error, f"Error fetching media info: {stderr}")
                return
            
            # Parse JSON output
            try:
                info = json.loads(stdout)
                GLib.idle_add(self.update_media_info, info)
            except json.JSONDecodeError:
                GLib.idle_add(self.show_error, "Failed to parse media information")
                
        except Exception as e:
            GLib.idle_add(self.show_error, f"Error: {str(e)}")
    
    def update_media_info(self, info):
        """Update media information display"""
        # Show the media info frame
        self.media_info_frame.show()
        
        # Update title
        title = info.get('title', 'Unknown')
        self.media_title.set_label(f"Title: {title}")
        
        # Update duration
        duration = info.get('duration', 0)
        if duration:
            minutes, seconds = divmod(duration, 60)
            hours, minutes = divmod(minutes, 60)
            if hours > 0:
                duration_str = f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                duration_str = f"{minutes}:{seconds:02d}"
        else:
            duration_str = "Unknown"
        self.media_duration.set_label(f"Duration: {duration_str}")
        
        # Try to load thumbnail
        thumbnail_url = info.get('thumbnail')
        if thumbnail_url:
            try:
                # Download thumbnail to temp file
                fd, temp_path = tempfile.mkstemp(suffix='.jpg')
                os.close(fd)
                
                thumbnail_cmd = [
                    'yt-dlp',
                    '-o', temp_path,
                    '--write-thumbnail',
                    '--convert-thumbnails', 'jpg',
                    '--no-download',
                    thumbnail_url
                ]
                
                process = subprocess.Popen(
                    thumbnail_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                process.wait()
                
                if os.path.exists(temp_path):
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file(temp_path)
                    # Scale to reasonable size
                    scaled_pixbuf = pixbuf.scale_simple(200, 150, GdkPixbuf.InterpType.BILINEAR)
                    self.media_thumbnail.set_from_pixbuf(scaled_pixbuf)
                    os.unlink(temp_path)
            except Exception as e:
                print(f"Error loading thumbnail: {e}")
    
    def on_fetch_qualities(self, widget):
        """Fetch available qualities for the URL"""
        url = self.url_entry.get_text().strip()
        if not url:
            self.show_error("Please enter a URL first")
            return
        
        # Also fetch media info when fetching qualities
        self.fetch_media_info()
        
        # Clear previous qualities
        self.quality_combo.remove_all()
        self.quality_combo.append_text("Fetching qualities...")
        self.quality_combo.set_active(0)
        
        # Run in thread to avoid blocking UI
        thread = threading.Thread(target=self.fetch_qualities_thread, args=(url,))
        thread.daemon = True
        thread.start()
    
    def fetch_qualities_thread(self, url):
        """Thread function to fetch qualities"""
        cookie_file = self.cookie_entry.get_text().strip()
        cmd = [
            'yt-dlp', 
            '--list-formats',
            '--no-warnings',
            url
        ]
        
        if cookie_file:
            cmd.extend(['--cookies', cookie_file])
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                GLib.idle_add(self.show_error, f"Error fetching qualities: {stderr}")
                return
            
            # Parse formats
            formats = []
            lines = stdout.split('\n')
            for line in lines:
                if line.strip() and ' ' in line and not line.startswith('['):
                    parts = line.split()
                    if len(parts) >= 3:
                        format_id = parts[0]
                        extension = parts[1]
                        resolution = parts[2] if len(parts) > 2 else "unknown"
                        
                        # Try to find filesize if available
                        filesize = ""
                        for part in parts:
                            if part.endswith('KiB') or part.endswith('MiB') or part.endswith('GiB'):
                                filesize = part
                                break
                        
                        format_str = f"{format_id} - {resolution} - {extension}"
                        if filesize:
                            format_str += f" - {filesize}"
                        formats.append((format_id, format_str))
            
            # Update UI on main thread
            GLib.idle_add(self.update_quality_combo, formats)
            
        except Exception as e:
            GLib.idle_add(self.show_error, f"Error: {str(e)}")
    
    def update_quality_combo(self, formats):
        """Update quality combo box with fetched formats"""
        self.quality_combo.remove_all()
        
        if not formats:
            self.quality_combo.append_text("No formats found")
            self.quality_combo.set_active(0)
            return
        
        # Add best and worst options
        self.quality_combo.append_text("best - Best quality (default)")
        self.quality_combo.append_text("worst - Worst quality")
        
        # Add all formats
        for format_id, format_str in formats:
            self.quality_combo.append_text(format_str)
        
        # Select best quality by default
        self.quality_combo.set_active(0)
    
    def on_add_to_queue(self, widget):
        """Add current URL to download queue"""
        url = self.url_entry.get_text().strip()
        if not url:
            self.show_error("Please enter a URL first")
            return
        
        # Add to queue list
        self.queue_list.append([url, "Queued", "0%"])
        self.download_queue.append(url)
        
        self.show_info(f"Added to queue: {url}")
    
    def process_queue(self):
        """Process the download queue"""
        if not self.download_queue or self.downloading:
            return
        
        if self.current_download_index + 1 < len(self.download_queue):
            self.current_download_index += 1
            next_url = self.download_queue[self.current_download_index]
            self.url_entry.set_text(next_url)
            
            # Update queue status
            tree_iter = self.queue_list.get_iter_from_string(str(self.current_download_index))
            self.queue_list.set_value(tree_iter, 1, "Downloading")
            
            # Start download
            self.on_download(None)
    
    def on_download(self, widget):
        """Start download process"""
        if self.downloading and not self.paused:
            self.show_error("Download already in progress")
            return
        
        url = self.url_entry.get_text().strip()
        if not url:
            self.show_error("Please enter a URL")
            return
        
        # If resuming a paused download
        if self.paused:
            self.paused = False
            self.pause_button.set_label("Pause")
            self.status_label.set_label("Resuming download...")
            return
        
        # Save to history (unless in incognito mode)
        self.save_history(url)
        
        # Get selected quality
        if self.quality_combo.get_active() < 0:
            self.show_error("Please select a quality")
            return
            
        quality_text = self.quality_combo.get_active_text()
        if not quality_text:
            self.show_error("Please select a quality")
            return
        
        # Parse quality (format id is the first part)
        if " - " in quality_text:
            quality = quality_text.split(" - ")[0]
        else:
            quality = quality_text
        
        # Get media type
        media_type = self.media_type_combo.get_active_text().lower()
        
        # Get format
        output_format = self.format_combo.get_active_text()
        
        # Get output path
        output_path = self.output_entry.get_text().strip()
        if not output_path:
            output_path = os.path.expanduser("~/Downloads")
        
        # Get cookie file
        cookie_file = self.cookie_entry.get_text().strip()
        
        # Get SponsorBlock option
        sponsorblock_option = self.sponsor_combo.get_active()
        sponsorblock_args = []
        if sponsorblock_option == 1:
            sponsorblock_args = ['--sponsorblock-remove', 'sponsor']
        elif sponsorblock_option == 2:
            sponsorblock_args = ['--sponsorblock-remove', 'sponsor,intro,outro']
        elif sponsorblock_option == 3:
            sponsorblock_args = ['--sponsorblock-remove', 'all']
        
        # Get metadata options
        metadata_args = []
        if self.embed_metadata.get_active():
            metadata_args.append('--embed-metadata')
        if self.embed_thumbnail.get_active() and media_type == 'video':
            metadata_args.append('--embed-thumbnail')
        
        # Build command based on media type
        cmd = ['yt-dlp']
        
        if media_type == 'audio':
            cmd.extend(['-x', '--audio-format', output_format])
        else:
            cmd.extend(['-f', f'{quality}+bestaudio/{quality}' if quality not in ['best', 'worst'] else quality])
            if output_format != 'best':
                cmd.extend(['--merge-output-format', output_format])
        
        cmd.extend([
            '-o', os.path.join(output_path, '%(title)s.%(ext)s'),
            '--newline',  # Get progress updates per line
            '--no-part',  # Don't use partial files (better for pause/resume)
        ])
        
        # Add optional arguments
        if cookie_file:
            cmd.extend(['--cookies', cookie_file])
        
        cmd.extend(sponsorblock_args)
        cmd.extend(metadata_args)
        cmd.append(url)
        
        # Update UI
        self.downloading = True
        self.paused = False
        self.download_button.set_sensitive(False)
        self.pause_button.set_sensitive(True)
        self.pause_button.set_label("Pause")
        self.stop_button.set_sensitive(True)
        self.progress_bar.set_fraction(0.0)
        self.status_label.set_label("Downloading...")
        
        # Clear log
        buffer = self.log_view.get_buffer()
        buffer.set_text("")
        
        # Run download in thread
        thread = threading.Thread(target=self.download_thread, args=(cmd,))
        thread.daemon = True
        thread.start()
    
    def download_thread(self, cmd):
        """Thread function to handle download"""
        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Read output line by line
            for line in iter(self.process.stdout.readline, ''):
                # Check if we're paused
                while self.paused and self.downloading:
                    time.sleep(0.5)
                
                # Check if we're stopped
                if not self.downloading:
                    break
                
                GLib.idle_add(self.update_log, line)
                
                # Try to parse progress from line
                if '[download]' in line and '%' in line:
                    try:
                        percent_str = line.split('%')[0].split()[-1]
                        percent = float(percent_str) / 100.0
                        GLib.idle_add(self.progress_bar.set_fraction, percent)
                        
                        # Update queue progress if this is a queued download
                        if self.current_download_index >= 0:
                            tree_iter = self.queue_list.get_iter_from_string(str(self.current_download_index))
                            self.queue_list.set_value(tree_iter, 2, f"{percent_str}%")
                    except:
                        pass
                
                # Extract download filename
                if 'Destination:' in line:
                    try:
                        self.current_download_name = line.split('Destination:')[1].strip()
                        GLib.idle_add(self.status_label.set_label, f"Downloading: {os.path.basename(self.current_download_name)}")
                    except:
                        pass
            
            if self.process:
                self.process.stdout.close()
                return_code = self.process.wait()
                
                if return_code == 0:
                    GLib.idle_add(self.download_finished, True, "Download completed successfully")
                    # Update queue status
                    if self.current_download_index >= 0:
                        tree_iter = self.queue_list.get_iter_from_string(str(self.current_download_index))
                        self.queue_list.set_value(tree_iter, 1, "Completed")
                        self.queue_list.set_value(tree_iter, 2, "100%")
                else:
                    GLib.idle_add(self.download_finished, False, f"Download failed with code {return_code}")
                    # Update queue status
                    if self.current_download_index >= 0:
                        tree_iter = self.queue_list.get_iter_from_string(str(self.current_download_index))
                        self.queue_list.set_value(tree_iter, 1, "Failed")
                
        except Exception as e:
            GLib.idle_add(self.download_finished, False, f"Error: {str(e)}")
    
    def on_pause(self, widget):
        """Pause or resume download"""
        if self.downloading:
            if self.paused:
                # Resume download
                self.paused = False
                self.pause_button.set_label("Pause")
                self.status_label.set_label("Resuming download...")
            else:
                # Pause download
                self.paused = True
                self.pause_button.set_label("Resume")
                self.status_label.set_label("Download paused")
    
    def on_stop(self, widget):
        """Stop download"""
        if self.downloading and self.process:
            self.process.terminate()
            self.downloading = False
            self.paused = False
            self.status_label.set_label("Download stopped")
            self.download_button.set_sensitive(True)
            self.pause_button.set_sensitive(False)
            self.stop_button.set_sensitive(False)
            self.pause_button.set_label("Pause")
            
            # Update queue status if this was a queued download
            if self.current_download_index >= 0:
                tree_iter = self.queue_list.get_iter_from_string(str(self.current_download_index))
                self.queue_list.set_value(tree_iter, 1, "Stopped")
    
    def on_open_browser(self, widget):
        """Open URL in built-in browser"""
        url = self.cookie_url_entry.get_text().strip()
        if not url:
            self.show_error("Please enter a URL first")
            return
        
        if not url.startswith('http'):
            url = 'https://' + url
        
        self.web_view.load_uri(url)
    
    def on_extract_cookies(self, widget):
        """Extract cookies from webview"""
        # Create a temporary file for cookies
        if self.temp_cookie_file:
            try:
                os.unlink(self.temp_cookie_file)
            except:
                pass
        
        fd, self.temp_cookie_file = tempfile.mkstemp(suffix='.txt')
        os.close(fd)
        
        # Get cookies from webview and save to file
        self.cookie_manager.get_cookies(self.web_view.get_uri(), None, self.on_cookies_fetched, None)
    
    def on_cookies_fetched(self, manager, result, user_data):
        """Callback for cookie fetching"""
        try:
            cookies = manager.get_cookies_finish(result)
            
            with open(self.temp_cookie_file, 'w') as f:
                f.write("# Netscape HTTP Cookie File\n")
                f.write("# Extracted by GRAB\n\n")
                
                for cookie in cookies:
                    domain = cookie.get_domain()
                    if domain.startswith('.'):
                        flag = "TRUE"
                    else:
                        flag = "FALSE"
                    
                    path = cookie.get_path() or "/"
                    secure = "TRUE" if cookie.is_secure() else "FALSE"
                    expires = str(int(cookie.get_expires().to_unix())) if cookie.get_expires() else "0"
                    name = cookie.get_name()
                    value = cookie.get_value()
                    
                    f.write(f"{domain}\t{flag}\t{path}\t{secure}\t{expires}\t{name}\t{value}\n")
            
            self.cookie_entry.set_text(self.temp_cookie_file)
            self.show_info("Cookies extracted successfully!")
            
        except Exception as e:
            self.show_error(f"Error extracting cookies: {str(e)}")
    
    def on_save_cookies(self, widget):
        """Save extracted cookies to app data"""
        if not self.temp_cookie_file or not os.path.exists(self.temp_cookie_file):
            self.show_error("No cookies to save. Please extract cookies first.")
            return
        
        # Ask for a name for the cookies
        dialog = Gtk.Dialog(
            title="Save Cookies",
            parent=self.window,
            flags=0,
            buttons=(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_SAVE, Gtk.ResponseType.OK
            )
        )
        
        dialog.set_default_size(300, 100)
        
        content_area = dialog.get_content_area()
        name_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        content_area.pack_start(name_box, True, True, 0)
        
        name_label = Gtk.Label(label="Name:")
        name_box.pack_start(name_label, False, False, 0)
        
        name_entry = Gtk.Entry()
        name_entry.set_placeholder_text("e.g., YouTube, Netflix")
        name_box.pack_start(name_entry, True, True, 0)
        
        content_area.show_all()
        
        response = dialog.run()
        cookie_name = name_entry.get_text().strip()
        dialog.destroy()
        
        if response != Gtk.ResponseType.OK or not cookie_name:
            return
        
        # Save cookies to app data directory
        cookie_dir = os.path.expanduser("~/.grab/cookies")
        os.makedirs(cookie_dir, exist_ok=True)
        
        cookie_file = os.path.join(cookie_dir, f"{cookie_name}.txt")
        shutil.copy2(self.temp_cookie_file, cookie_file)
        
        # Update saved cookies list
        self.load_saved_cookies()
        self.show_info(f"Cookies saved as '{cookie_name}'")
    
    def on_save_settings(self, widget):
        """Save application settings"""
        self.default_format = self.default_format_combo.get_active()
        self.default_media_type = self.default_media_type_combo.get_active()
        self.default_output_path = self.default_output_entry.get_text().strip()
        
        self.save_settings()
        self.show_info("Settings saved successfully!")
    
    def on_backup_settings(self, widget):
        """Backup settings to a file"""
        dialog = Gtk.FileChooserDialog(
            title="Backup Settings",
            parent=self.window,
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
        
        dialog.set_current_name("grab_backup.json")
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            backup_file = dialog.get_filename()
            # Ensure it has .json extension
            if not backup_file.endswith('.json'):
                backup_file += '.json'
            
            # Create backup data
            backup_data = {
                'settings': {
                    'use_dark_theme': self.use_dark_theme,
                    'theme_follows_system': self.theme_follows_system,
                    'default_format': self.default_format,
                    'default_media_type': self.default_media_type,
                    'default_output_path': self.default_output_path,
                    'sponsorblock': self.default_sponsorblock,
                    'embed_metadata': self.default_embed_metadata,
                    'embed_thumbnail': self.default_embed_thumbnail
                },
                'cookies': {}
            }
            
            # Backup cookies
            cookie_dir = os.path.expanduser("~/.grab/cookies")
            if os.path.exists(cookie_dir):
                for cookie_file in os.listdir(cookie_dir):
                    if cookie_file.endswith('.txt'):
                        with open(os.path.join(cookie_dir, cookie_file), 'r') as f:
                            backup_data['cookies'][cookie_file] = f.read()
            
            # Write backup file
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=4)
            
            self.show_info(f"Settings backed up to {backup_file}")
        
        dialog.destroy()
    
    def on_restore_settings(self, widget):
        """Restore settings from a backup file"""
        dialog = Gtk.FileChooserDialog(
            title="Restore Settings",
            parent=self.window,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        # Add filter for JSON files
        filter_json = Gtk.FileFilter()
        filter_json.set_name("JSON files")
        filter_json.add_mime_type("application/json")
        dialog.add_filter(filter_json)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            backup_file = dialog.get_filename()
            
            try:
                with open(backup_file, 'r') as f:
                    backup_data = json.load(f)
                
                # Restore settings
                if 'settings' in backup_data:
                    with open(self.settings_file, 'w') as f:
                        json.dump(backup_data['settings'], f, indent=4)
                    
                    # Reload settings
                    self.load_settings()
                
                # Restore cookies
                if 'cookies' in backup_data:
                    cookie_dir = os.path.expanduser("~/.grab/cookies")
                    os.makedirs(cookie_dir, exist_ok=True)
                    
                    for cookie_file, content in backup_data['cookies'].items():
                        with open(os.path.join(cookie_dir, cookie_file), 'w') as f:
                            f.write(content)
                    
                    # Reload cookies
                    self.load_saved_cookies()
                
                self.show_info("Settings restored successfully!")
                
            except Exception as e:
                self.show_error(f"Error restoring settings: {str(e)}")
        
        dialog.destroy()
    
    def update_log(self, text):
        """Update log view with new text"""
        buffer = self.log_view.get_buffer()
        end_iter = buffer.get_end_iter()
        buffer.insert(end_iter, text)
        
        # Scroll to end
        mark = buffer.get_insert()
        end_iter = buffer.get_end_iter()
        buffer.place_cursor(end_iter)
        self.log_view.scroll_to_mark(mark, 0.0, True, 0.0, 1.0)
    
    def download_finished(self, success, message):
        """Handle download completion"""
        self.downloading = False
        self.paused = False
        self.download_button.set_sensitive(True)
        self.pause_button.set_sensitive(False)
        self.stop_button.set_sensitive(False)
        self.pause_button.set_label("Pause")
        self.status_label.set_label(message)
        
        if success:
            self.progress_bar.set_fraction(1.0)
            # Process next item in queue
            GLib.timeout_add(1000, self.process_queue)  # Wait 1 second before next download
        else:
            self.progress_bar.set_fraction(0.0)
    
    def on_report_error(self, widget):
        """Open yt-dlp issue page in browser"""
        import webbrowser
        webbrowser.open("https://github.com/yt-dlp/yt-dlp/issues/new")
    
    def show_error(self, message):
        """Show error dialog"""
        dialog = Gtk.MessageDialog(
            parent=self.window,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=message
        )
        dialog.run()
        dialog.destroy()
    
    def show_info(self, message):
        """Show info dialog"""
        dialog = Gtk.MessageDialog(
            parent=self.window,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=message
        )
        dialog.run()
        dialog.destroy()
    
    def on_destroy(self, widget):
        """Handle window close"""
        if self.downloading and self.process:
            self.process.terminate()
        
        # Clean up temporary cookie file
        if self.temp_cookie_file and os.path.exists(self.temp_cookie_file):
            try:
                os.unlink(self.temp_cookie_file)
            except:
                pass
        
        # Save settings
        self.save_settings()
        
        Gtk.main_quit()

if __name__ == "__main__":
    app = GRABApp()
    Gtk.main()
