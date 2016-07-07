# Cookbook Name:: mopidy-jukebox
# Recipe:: default

include_recipe 'build-essential::default'

%w{libsqlite3-dev libffi-dev gstreamer1.0-fluendo-mp3 gstreamer1.0-plugins-bad gstreamer1.0-alsa gstreamer1.0-plugins-good gstreamer1.0-plugins-ugly libssl-dev gir1.2-gstreamer-1.0 gir1.2-gst-plugins-base-1.0 python-dev python-gi cron git}.each do |pkg|
	package pkg do
		action :install
	end
end

python_runtime '2'

files_default = File.realpath(File.join(File.dirname(__FILE__), "..", "files/default"))

# This is a horrible hack, and I really should be using the local libraries in a different way
ruby_block "remove local libraries" do
  block do
    rc = Chef::Util::FileEdit.new(File.join(files_default, "requirements.txt"))
    rc.search_file_delete_line(
      /^-e mopidy.*$/
    )
    rc.write_file
  end
end

pip_requirements File.join(files_default, "requirements.txt") do
	options "--exists-action w"
	action :install
end

execute 'install mopidy-cacher' do
	cwd File.join(files_default, "mopidy-cacher")
	command 'pip install -e .'
end

execute 'install mopidy-musicbox-webclient' do
	cwd File.join(files_default, "mopidy-musicbox-webclient")
	command 'pip install -e .'
end

user 'mopidy' do
	comment 'Mopidy'
	system true
	shell '/bin/false'
	home '/home/mopidy'
	supports :manage_home => true
end

execute 'reload systemd' do
	command 'systemctl daemon-reload && systemctl enable mopidy.service'
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

cookbook_file "/etc/mopidy/mopidy-local.conf" do
	action :create_if_missing
	source "mopidy-local.conf"
	owner "mopidy"
	mode "0644"
end

cron 'cache update' do
  action :create
  minute '0'
  hour '0'
  user 'root'
  mailto 'palfrey@lshift.net'
  command "/usr/local/bin/mopidy --config /etc/mopidy/mopidy.conf:/etc/mopidy/mopidy-local.conf cacher 1>/root/mopidy-cacher.log 2>&1"
end

cron 'local scan' do
  action :create
  minute '0'
  hour '4'
  user 'root'
  mailto 'palfrey@lshift.net'
  command "/usr/local/bin/mopidy --config /etc/mopidy/mopidy.conf:/etc/mopidy/mopidy-local.conf local scan 1>/root/mopidy-scan.log 2>&1"
end

service 'mopidy' do
	provider Chef::Provider::Service::Systemd
	action [:enable, :start]
end

if node["lsb"]["id"] == "Raspbian"
	package "luakit" do
		action :install
	end
else
	Chef::Log.info("Running Debian, not Raspbian, so no luakit")
end

%w{lxde-core lxsession lxlauncher nginx lightdm}.each do |pkg|
	package pkg do
		action :install
	end
end

service 'nginx' do
	provider Chef::Provider::Service::Systemd
	action [:enable, :start]
end

cookbook_file "/etc/nginx/sites-available/default" do
	source "nginx.conf"
	owner "root"
	mode "0644"
	notifies :reload, 'service[nginx]', :immediately
end
