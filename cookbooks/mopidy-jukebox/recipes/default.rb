# Cookbook Name:: mopidy-jukebox
# Recipe:: default

%w{libsqlite3-dev libffi-dev gstreamer1.0-fluendo-mp3 gstreamer1.0-plugins-bad gstreamer1.0-alsa gstreamer1.0-plugins-good gstreamer1.0-plugins-ugly libssl-dev gir1.2-gstreamer-1.0 gir1.2-gst-plugins-base-1.0 python-dev python-gi}.each do |pkg|
	package pkg do
		action :install
	end
end

include_recipe "python::pip"

files_default = File.realpath(File.join(File.dirname(__FILE__), "..", "files/default"))

python_pip File.join(files_default, "requirements.txt") do
	options "-r"
	action :install
end

execute 'install mopidy-cacher' do
	cwd File.join(files_default, "mopidy-cacher")
	command 'python setup.py develop'
	not_if 'pip list | grep Mopidy-Cacher'
end

execute 'install mopidy-musicbox-webclient' do
	cwd File.join(files_default, "mopidy-musicbox-webclient")
	command 'python setup.py develop'
	not_if 'pip list | grep Mopidy-MusicBox-Webclient'
end
