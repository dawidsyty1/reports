# Options report generator.
Following tool preparing reports and putting them into the google bucket. Reports contain information use in my mid-term and long-term investment strategies.

As a main libraries I'm using https://openbb.co/ and https://technical-analysis-library-in-python.readthedocs.io/en/latest/, which help to me a manage and display charts and plots, build HTML reports. My main strategies contains PUT/CALL options and Fear/Greed analysis.


# Setup
Create .env file with:

    GOOGLE_APPLICATION_CREDENTIALS=""
    SMTP_API_KEY=""
    BUCKET_NAME=""
    LOGLEVEL=""
    SENDER_NAME=""
    SENDER_EMAIL=""
    RECEIVER_NAME=""

Build docker

    make builddev

Generate simple HTML report:
    make generate
