#!/usr/bin/env ruby

require_relative 'flickr_auth'
require 'pry'

flickr = flickr_auth

albums = flickr.photosets.getList.map(&:title)
directories = Dir.entries('/home/paul/Pictures/nailarts') - ['.', '..'] - albums

directories.each do |directory|
  photo_paths = Dir.entries("/home/paul/Pictures/nailarts/#{directory}") - ['.', '..']

  flickr_photos = []
  photo_paths.each do |photo_path|
    flickr_photos << flickr.upload_photo("/home/paul/Pictures/nailarts/#{directory}/#{photo_path}")
  end

  photoset = flickr.photosets.create(title: directory, primary_photo_id: flickr_photos[0])
  flickr_photos.shift
  while flickr_photos.length != 0
    flickr.photosets.addPhoto(photoset_id: photoset.id, photo_id: flickr_photos[0])
    flickr_photos.shift
  end
end
