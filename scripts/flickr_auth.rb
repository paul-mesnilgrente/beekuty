require 'flickr'

def flickr_auth
  puts "flickr_auth"
  flickr = Flickr.new(ENV['FLICKR_API_KEY'], ENV['FLICKR_SHARED_SECRET'])
  puts "flickr_auth2"

  if ENV['FLICKR_ACCESS_TOKEN'] && ENV['FLICKR_ACCESS_SECRET']
    flickr.access_token = ENV['FLICKR_ACCESS_TOKEN']
    flickr.access_secret = ENV['FLICKR_ACCESS_SECRET']
  else
    # authentication
    token = flickr.get_request_token
    auth_url = flickr.get_authorize_url(token['oauth_token'], :perms => 'delete')

    puts "Open this url in your browser to complete the authentication process: #{auth_url}"
    puts "Copy here the number given when you complete the process."
    verify = gets.strip

    flickr.get_access_token(token['oauth_token'], token['oauth_token_secret'], verify)
    login = flickr.test.login
    puts "You are now authenticated as #{login.username} with token #{flickr.access_token} and secret #{flickr.access_secret}"
    puts "export FLICKR_ACCESS_TOKEN=#{flickr.access_token}"
    puts "export FLICKR_ACCESS_SECRET=#{flickr.access_secret}"
  end

  flickr
end
