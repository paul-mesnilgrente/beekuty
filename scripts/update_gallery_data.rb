#!/usr/bin/env ruby

require 'faraday'
require 'json'
require 'yaml'
require 'pry'
require 'launchy'
require 'date'

# Instagram module
module Instgrm
  # Used to stop the script when failing and log debugging logs
  class RequestException
    def initialize(exception)
      @exception = exception
    end

    def call
      binding.pry
      puts 'Request failed'
      exit 1
    end
  end

  # Create requests for instagram
  class Request
    def initialize
      @connection = Faraday.new(url: 'https://graph.instagram.com/') do |faraday|
        faraday.request :json
        faraday.response :json
        faraday.response :logger
        faraday.response :raise_error
      end
      @access_token_param = { access_token: ENV['INSTAGRAM_ACCESS_TOKEN'] }
    end

    def fetch_image(media_url)
      Faraday.new(media_url) { |faraday| faraday.response :raise_error }.get.body
    rescue Faraday::Error => e
      RequestException.new(e).call
    end

    def get(path, params)
      @connection.get(path, params.merge(@access_token_param)).body
    rescue Faraday::Error => e
      RequestException.new(e).call
    end
  end
end

def first_medias
  Instgrm::Request.new.get(
    '/me/media', { fields: 'id,children,caption,media_type,media_url,timestamp' }
  )
end

def download_image(media)
  image = Instgrm::Request.new.fetch_image(media['media_url'])
  return if File.exist?("assets/images/nailarts/#{media['id']}.jpg")

  File.open("assets/images/nailarts/#{media['id']}.jpg", 'wb') { |f| f.write(image) }
end

def fetch_child(id)
  Instgrm::Request.new.get("/#{id}", { fields: 'media_url' })
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
data = []
medias = first_medias
medias['data'].each do |media|
  data << download_media(media)
end

File.write('_data/gallery.yaml', data.to_yaml)

puts 'The end'
