# server.rb
#
# Use this sample code to handle webhook events in your integration.
#
# 1) Paste this code into a new file (server.rb)
#
# 2) Install dependencies
#   gem install sinatra
#   gem install stripe
#
# 3) Run the server on http://localhost:4242
#   ruby server.rb

require 'json'
require 'sinatra'
require 'stripe'

# The library needs to be configured with your account's secret key.
# Ensure the key is kept out of any version control system you might be using.
Stripe.api_key = 'sk_test_51PqfojRuchQD6pznB4Htxnco9P1h6phm3nFosqS2cmbNY2Ns0npH99GdXOqEvThw5ighc8OgBOqOiYlnVIVGe12I006p4WIFjs'

# This is your Stripe CLI webhook secret for testing your endpoint locally.
endpoint_secret = 'whsec_8f85abc58d6c2266535bc9006642c391a445dd82f92f7a47c1d63a343e10bfaa'

set :port, 4242

post '/webhook' do
    payload = request.body.read
    sig_header = request.env['HTTP_STRIPE_SIGNATURE']
    event = nil

    begin
        event = Stripe::Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    rescue JSON::ParserError => e
        # Invalid payload
        status 400
        return
    rescue Stripe::SignatureVerificationError => e
        # Invalid signature
        status 400
        return
    end

    # Handle the event
    case event.type
    when 'payment_intent.succeeded'
        payment_intent = event.data.object
    # ... handle other event types
    else
        puts "Unhandled event type: #{event.type}"
    end

    status 200
end