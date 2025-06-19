# Grade Calculator Bot

A Telegram bot for calculating academic averages for ENS (École Normale Supérieure) students.

## Features

- Calculate overall averages for different specializations (Math, Physics, Info, Sciences)
- Support for multiple levels and sub-levels
- Real-time grade validation
- User activity tracking
- Multi-language support (English/Arabic)
- Webhook-based deployment

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd grade-calculator-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create environment file:
```bash
cp .env.example .env
```

4. Configure environment variables in `.env`:
```
BOT_TOKEN=your_bot_token_here
ADMIN_ID=your_admin_id
WEBHOOK_HOST=your_webhook_host
DB_PATH=bot_newdata.db
```

## Usage

### Local Development
```bash
python Main.py
```

### Production Deployment
The bot is configured for deployment on Google Cloud Run with webhook support.

## Project Structure

```
├── Main.py                 # Main bot file
├── config.py              # Configuration management
├── database.py            # Database operations
├── error_handler.py       # Error handling utilities
├── grade_calculator.py    # Grade calculation logic
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Database Schema

- `visitors`: User tracking table
- `overall_average_count`: Usage statistics
- `visitor_count_table`: Visitor count tracking

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support, contact @yassineboukerma on Telegram. 