# Social Media OSINT & Analysis Tool 🕵️‍♂️

A powerful Python-based tool for social media analysis, OSINT (Open Source Intelligence), and digital investigation. This tool combines various techniques to gather information from social media platforms and perform location tracking.

![Tool Banner](https://raw.githubusercontent.com/shadowhackr/social-media-tools/main/banner.png)

## 🌟 Features

- 🎯 **Location Tracking**
  - Track targets through social engineering links
  - Cell tower triangulation
  - Real-time location monitoring

- 🔍 **Social Media Analysis**
  - Find accounts linked to phone numbers
  - Reverse phone lookup from usernames
  - Twitter source analysis
  - Instagram activity monitoring
  - Facebook Messenger tracking

- 📱 **Phone Number Intelligence**
  - Carrier information
  - Location history
  - Associated social media accounts
  - Cell tower mapping

## 📋 Requirements

- Python 3.8+
- Chrome Browser
- Active Internet Connection

### Required Python Packages
```bash
pip install -r requirements.txt
```

## 🛠️ Installation

1. Clone the repository:
```bash
git clone https://github.com/ShadowHackrs/Social-Media-OSINT.git
cd Social-Media-OSINT
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Configure API Keys (Optional):
   - Create a `config.py` file
   - Add your Twitter API keys if you want to use Twitter functionality:
```python
TWITTER_API_KEYS = {
    'consumer_key': 'your_consumer_key',
    'consumer_secret': 'your_consumer_secret',
    'access_token': 'your_access_token',
    'access_token_secret': 'your_access_token_secret'
}
```

## 🚀 Usage

1. Run the tool:
```bash
python social_media_tools.py
```

2. Choose from available options:
   - Track Location (Option 1)
   - Cell Tower Tracker (Option 2)
   - Find Social Media Accounts (Option 3)
   - Find Phone Numbers (Option 4)
   - Monitor Messenger (Option 5)
   - Monitor Instagram (Option 6)
   - Analyze Tweets (Option 7)
   - Track Phone Towers (Option 8)

## 📝 Configuration

### Twitter API Setup (Optional)
1. Create a Twitter Developer account
2. Create a new application
3. Get your API keys and tokens
4. Add them to `config.py`

### Chrome Driver
- The tool uses Selenium with Chrome
- Make sure you have Chrome browser installed
- ChromeDriver will be automatically downloaded

## ⚠️ Disclaimer

This tool is for educational purposes only. Users are responsible for complying with applicable laws and regulations. The developer is not responsible for any misuse or damage caused by this tool.

## 🔒 Privacy & Security

- Don't share your API keys
- Use a VPN when necessary
- Respect privacy laws and terms of service
- Don't use for unauthorized surveillance

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Contact

- Website: [https://www.shadowhackr.com](https://www.shadowhackr.com)
- Facebook: [Tareq.DJX](https://www.facebook.com/Tareq.DJX)
- Instagram: [@shadowhackr](https://www.instagram.com/shadowhackr)

## 🙏 Acknowledgments

- Thanks to all contributors
- Special thanks to the open-source community

## 📊 Version History

- v1.0.0 (Initial Release)
  - Basic social media analysis
  - Location tracking features
  - Phone number intelligence

---
Created with ❤️ by ShadowHackr
