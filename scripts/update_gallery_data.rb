#!/usr/bin/env ruby

require 'faraday'
require 'json'
require 'yaml'
require 'pry'
require 'launchy'
require 'date'

# visit
unless ENV['INSTAGRAM_ACCESS_TOKEN']
  params = [
    "client_id=#{ENV['INSTAGRAM_APP_ID']}",
    "redirect_uri=https://beekuty.fr/auth",
    "scope=user_profile,user_media",
    "response_type=code"
  ]
  Launchy.open("https://api.instagram.com/oauth/authorize?#{params.join('&')}")

  print 'Please enter the code (excluding #): '
  code = gets.chomp

  codesResponse = Faraday.post('https://api.instagram.com/oauth/access_token', {
    client_id: ENV['INSTAGRAM_APP_ID'],
    client_secret: ENV['INSTAGRAM_APP_SECRET'],
    grant_type: 'authorization_code',
    redirect_uri: 'https://beekuty.fr/auth',
    code: code
  })

  # Exchanging the code against a token:
  response_json = JSON.parse(codesResponse.body)
  unless response_json['access_token']
    puts "ERROR when getting the access_token with #{ENV['INSTAGRAM_AUTH_CODE']}"
    puts response_json
    exit 1
  end

  puts ''
  puts 'Please run:'
  puts "export INSTAGRAM_ACCESS_TOKEN=#{response_json['access_token']}"
  puts "export INSTAGRAM_USER_ID=#{response_json['user_id']}"
  puts "And run the script again"

  exit 0
end

# get the media
mediasResponse = Faraday.get('https://graph.instagram.com/me/media', {
  fields: 'id,children,caption,media_type,media_url,timestamp',
  access_token: ENV['INSTAGRAM_ACCESS_TOKEN']
})

allMedias = JSON.parse(mediasResponse.body)

################
# ADD PAGINATION
################
data = []
allMedias['data'].each do |media|
  next unless media['media_type'] == 'IMAGE'
  if media['media_type'] == 'IMAGE'
    data << {
      'id' => media['id'],
      'media_type' => 'image',
      'url' => media['media_url'],
      'date' => Date.parse(media['timestamp']).strftime('%d/%m/%Y')
    }
    response = Faraday.get(media['media_url'])
    if response.success?
      if !File.exists?("assets/images/nailarts/#{media['id']}.jpg")
        File.open("assets/images/nailarts/#{media['id']}.jpg", 'wb') { |f| f.write(response.body) }
      end
    else
      puts "Failed to download #{media['id']}"
    end
  elsif media['media_type'] == 'CAROUSEL_ALBUM'
    children = []
    media['children']['data'].each do |child|
      childResponse = Faraday.get("https://graph.instagram.com/#{child['id']}", {
        fields: 'media_url',
        access_token: ENV['INSTAGRAM_ACCESS_TOKEN']
      })
      children << JSON.parse(childResponse.body)['media_url']
    end
    data << {
      'type' => 'album',
      'url' => media['media_url'],
      'date' => Date.parse(media['timestamp']).strftime('%d/%m/%Y'),
      'children' => children
    }
  end
end

File.write('_data/gallery.yaml', data.to_yaml)

puts 'The end'
