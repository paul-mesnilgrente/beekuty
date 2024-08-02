#!/usr/bin/env ruby

require 'faraday'
require 'json'
require 'yaml'
require 'pry'
require 'launchy'
require 'date'

class RequestException
  def initialize(response, exception)
    @response = response
    @exception = exception
  end

  def call
    binding.pry
    puts 'Request failed'
    exit 1
  end
end

def first_medias
  medias_response = Faraday.get(
    'https://graph.instagram.com/me/media', {
      fields: 'id,children,caption,media_type,media_url,timestamp',
      access_token: ENV['INSTAGRAM_ACCESS_TOKEN']
    }
  )
  JSON.parse(medias_response.body)
end

def download_image(media)
  response = Faraday.get(media['media_url'])
  if response.success?
    unless File.exist?("assets/images/nailarts/#{media['id']}.jpg")
      File.open("assets/images/nailarts/#{media['id']}.jpg", 'wb') { |f| f.write(response.body) }
    end
  else
    puts "Failed to download #{media['id']}"
  end
end

def fetch_child(id)
  response = Faraday.get(
    "https://graph.instagram.com/#{id}", {
      fields: 'media_url',
      access_token: ENV['INSTAGRAM_ACCESS_TOKEN']
    }
  )
  JSON.parse(response.body)
end

def download_children(media)
  children = []
  media['children']['data'].each do |child|
    child_response = fetch_child(child['id'])
    download_image(child_response)
    children << child_response
  end
  children
end

def build_data(media)
  {
    'id' => media['id'],
    'media_type' => media['media_type'],
    'url' => media['media_url'],
    'caption' => media['caption'],
    'timestamp' => media['timestamp']
  }
end

def download_media(media)
  data = build_data(media)

  if media['media_type'] == 'IMAGE'
    download_image(media)
  elsif media['media_type'] == 'CAROUSEL_ALBUM'
    data['children'] = download_children(media)
  end

  data
end

# get the media

medias = first_medias

################
# ADD PAGINATION
################
data = []
medias['data'].each do |media|
  data << download_media(media)
end

File.write('_data/gallery.yaml', data.to_yaml)

puts 'The end'
