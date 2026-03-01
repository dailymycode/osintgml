# OSINTGML

<p align="center">
  <img src="logo.png" alt="OSINTGML logo" width="200">
</p>

Account recovery + email variations — CLI tools.

## Demo

![OSINTGML demo](demo.gif)

- **Account recovery**: username/email → masked contact info (forgot password flows).
- **Email variations**: masked email + optional first/last name, numbers, username → candidate emails.

## Run

```bash
pip install -r requirements.txt
python main.py
```

Set `GEMINI_API_KEY` in `.env` (or export) for email variations.
