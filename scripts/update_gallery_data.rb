#!/usr/bin/env ruby

require 'faraday'
require 'json'
require 'yaml'
require 'pry'
require 'launchy'
require 'date'

if ENV.fetch('INSTAGRAM_ACCESS_TOKEN', nil).nil?
  puts 'Please export INSTAGRAM_ACCESS_TOKEN'
  exit 1
end

puts 'before'
puts "ENV #{ENV.fetch('INSTAGRAM_ACCESS_TOKEN', nil).class}"
puts "ENV #{ENV.fetch('INSTAGRAM_ACCESS_TOKEN', nil).length}"
puts 'after'

# Instagram module
module Instgrm
  # Used to stop the script when failing and log debugging logs
  class RequestException
    def initialize(exception)
      @exception = exception
    end

    def call
      puts 'REQUEST FAILED'
      puts @exception.class
      puts "STATUS: #{@exception.response_status}"
      puts "HEADERS: #{@exception.response_headers}"
      puts "BODY: #{@exception.response_body}"
      binding.pry
      exit 1
    end
  end

  # Create requests for instagram
  class Api
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

def fetch_medias(last_response)
  if last_response.nil?
    Instgrm::Api.new.get(
      '/me/media', { fields: 'id,children,caption,media_type,media_url,timestamp' }
    )
  else
    return nil if last_response['paging']['next'].nil?

    Instgrm::Api.new.get(
      last_response['paging']['next'], { fields: 'id,children,caption,media_type,media_url,timestamp' }
    )
  end
end

# media_url can be used to avoid downloading images
# this method is kept in case it's needed again
def download_image(media)
  return if ENV.fetch('DOWNLOAD_IMAGES', 'false') == 'false'

  image_path = "assets/images/nailarts/#{media['id']}.jpg"
  return if File.exist?(image_path)

  image = Instgrm::Api.new.fetch_image(media['media_url'])
  File.open(image_path, 'wb') { |f| f.write(image) }
end

def fetch_child(id)
  Instgrm::Api.new.get("/#{id}", { fields: 'media_url' })
end

def download_children(media)
  children = []
  media['children']['data'].each do |child|
    child_response = fetch_child(child['id'])
    # media_url can be used to avoid downloading images
    download_image(child_response)
    children << { id: child_response['id'], media_url: child_response['media_url'] }
  end
  children
end

def build_data(media)
  {
    id: media['id'],
    media_type: media['media_type'],
    caption: media['caption'],
    timestamp: media['timestamp'],
    media_url: media['media_url']
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

# used to store
class Gallery
  FILE_PATH = '_data/gallery.json'.freeze

  def initialize
    @data = []
  end

  def first_id
    return nil if @data.empty?

    @data.first['id']
  end

  def add(item)
    @data.unshift(item)
  end

  def load
    return nil unless File.exist?(FILE_PATH)

    @data = JSON.parse(File.read(FILE_PATH))
  end

  def save
    File.write(FILE_PATH, @data.to_json)
  end
end

# used to simplify the script reading
class ProgressLogger
  def initialize
    @page = 0
  end

  def log_new_page
    @page += 1
    log("Processing page #{@page}...")
  end

  def log_fetched_all(id)
    log("Found the latest id #{id}")
  end

  def log_data_writing
    log('Writing data')
  end

  def log_end
    log('END')
  end

  private

  def log(message)
    puts ''
    puts '#######################################'
    puts "# #{message}"
    puts '#######################################'
    puts ''
  end
end

logger = ProgressLogger.new
gallery = Gallery.new
gallery.load
first_id = gallery.first_id

response = nil
fetched_all = false
while !fetched_all && (response = fetch_medias(response))
  logger.log_new_page

  response['data'].each do |media|
    if media['id'] == first_id
      fetched_all = true
      logger.log_fetched_all(first_id)
      break
    end

    gallery.add(download_media(media))
  end
end

logger.log_data_writing
gallery.save

logger.log_end
