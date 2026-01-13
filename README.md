# Youtube-Galaxy
Predict controversies with influencers before they happen, based upon trends of current influencers on the respective platforms

Problems:
- Bias: Going to r/livestreamfails or youtube comments ona  topic that is sensitive already causes HEAVY bias. 


## Things we overcame:
- Balance of Pricing vs time:
    * By using the Gemini pricing, we'd be limited to 60 comments per minute since that's what's allowed. We would need to:
      * Why it's 100% Free: It gives you a permanent free-of-charge tier with a rate limit of 60 queries per minute (QPM).

        The Trade-off: You exactly identified it: "We dont need to worry about time."

            If you have 20,000 comments, it will take 20,000 / 60 = 333 minutes (about 5.5 hours) to process them all.

            Your analyzer.py script will just run in your terminal for 6 hours, politely respecting the 60 QPM limit, and it will cost you $0.00.

        Model Quality: It's fantastic. You can use a model like gemini-1.5-flash and give it a prompt to return both sentiment and the scandal topic in one go, saving you even more time.
    
    * Better option: Use a local model(s). Hugging face
        * What it is: Instead of calling an API, you download a pre-trained, open-source model from Hugging Face and run it on your own computer using the transformers library.

        Pros:

            100% Free, Forever: No API keys, no rate limits.

            FAST: If you have a decent computer (especially with a GPU), this will be much faster than the 6-hour rate-limited Gemini API.

            Impressive Skill: This is a very good skill to show. It's what MLOps engineers do.

        Cons (for this MVP):

            More Complex: The code is more complex than a simple API call.

            "Dumber" Models: You would need two separate models:

                A small, fast sentiment model (easy).

                A separate topic extraction model (much harder).

            This complexity can slow you down, which is exactly what you wanted to avoid.

* Learned along the way
    - Must truncate texts due to token limitations of models

* For embedding models:
    The Problem with "Last 50 Videos"

You suggested grabbing the last 50 video titles and descriptions. While more data is usually better, we hit two technical bottlenecks here:

    The Context Window (Token Limit): The model we are using (all-MiniLM-L6-v2) has a limit (usually 256 or 384 tokens). 50 video titles + descriptions will result in thousands of tokens. The model will simply chop off the last 90% of your text. It won't even "see" videos 6 through 50.

    The Noise Ratio: Video descriptions are often full of "boilerplate" junk: Merch links, social media handles, affiliate codes, and copyright disclaimers. This is "noise" that dilutes the "signal" (the actual topic).

    