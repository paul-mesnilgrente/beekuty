#!/usr/bin/env ruby

require 'faraday'
require 'json'
require 'yaml'
require 'pry'
require 'launchy'
require 'date'

params = [
  "client_id=#{ENV['INSTAGRAM_APP_ID']}",
  'redirect_uri=https://beekuty.fr/auth',
  'scope=user_profile,user_media',
  'response_type=code'
]
Launchy.open("https://api.instagram.com/oauth/authorize?#{params.join('&')}")

print 'Please enter the code (excluding #): '
code = gets.chomp

codes_response = Faraday.post(
  'https://api.instagram.com/oauth/access_token', {
    client_id: ENV['INSTAGRAM_APP_ID'],
    client_secret: ENV['INSTAGRAM_APP_SECRET'],
    grant_type: 'authorization_code',
    redirect_uri: 'https://beekuty.fr/auth',
    code: code
  }
)

# Exchanging the code against a token:
response_json = JSON.parse(codes_response.body)
unless response_json['access_token']
  puts "ERROR when getting the access_token with #{ENV['INSTAGRAM_AUTH_CODE']}"
  puts response_json
  exit 1
end

puts ''
puts 'Please run:'
puts "export INSTAGRAM_ACCESS_TOKEN=#{response_json['access_token']}"
puts "export INSTAGRAM_USER_ID=#{response_json['user_id']}"
puts 'And run`./scripts/update_gallery_data.rb`'

exit 0
