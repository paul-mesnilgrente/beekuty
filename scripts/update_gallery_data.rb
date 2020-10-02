#!/usr/bin/env ruby

require_relative 'flickr_auth'
require 'pry'

flickr = flickr_auth

binding.pry

albums = flickr.photosets.getList()

sorted_albums = {}
albums.each { |album| sorted_albums[album.title] = album }
sorted_albums = sorted_albums.sort_by { |key| key }.reverse.to_h

gallery_photos = []
sorted_albums.values.each do |album|
  photo_sizes = flickr.photos.getSizes(photo_id: album.primary)

  sizes = {}
  photo_sizes.each do |photo_size|
    sizes[photo_size.label.downcase.gsub(' ', '_')] = {
      width: photo_size.width,
      height: photo_size.height,
      source: photo_size.source,
      url: photo_size.url
    }
  end
  gallery_photos << sizes
end

File.write('_data/gallery.yaml', gallery_photos.to_yaml)

puts "THE END"
