# Troubleshooting
If you're having problems with this application, first check the log file at latest.log.

Problems with the OpenAI API almost always stem from the API key. Make sure it's valid and try again.
If you don't have one, you can get one [here](https://beta.openai.com/signup/). Make sure to add some funds to it.
You can expect a single image to cost around a max of 0.1 USD.

If your API access is new, you might have a low rate limit.
This means you can only make a few requests per minute. If processing takes long because of this, 
it isn't a problem with the script, but with the API itself.

Also, make sure you're starting this script from your platform's included script to ensure dependencies are installed.

This should go without saying, but you should have python installed as well.
