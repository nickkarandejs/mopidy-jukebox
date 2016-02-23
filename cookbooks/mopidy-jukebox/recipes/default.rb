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
	command 'python setup.py install'
end

execute 'install mopidy-musicbox-webclient' do
	cwd File.join(files_default, "mopidy-musicbox-webclient")
	command 'python setup.py install'
end

user 'mopidy' do
	comment 'Mopidy'
	system true
	shell '/bin/false'
	home '/home/mopidy'
	supports :manage_home => true
end

execute 'reload systemd' do
	command 'systemctl daemon-reload'
	action :nothing
end

cookbook_file "/etc/systemd/system/mopidy.service" do
	source "mopidy.service"
	owner "root"
	group "root"
	mode "0644"
	notifies :run, 'execute[reload systemd]', :immediately
end

directory '/etc/mopidy' do
	owner 'mopidy'
	mode '0755'
	action :create
end

cookbook_file "/etc/mopidy/mopidy.conf" do
	source "mopidy.conf"
	owner "mopidy"
	mode "0644"
end

service 'mopidy' do
	provider Chef::Provider::Service::Systemd
	action :start
end
