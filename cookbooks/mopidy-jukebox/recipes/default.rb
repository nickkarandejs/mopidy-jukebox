# Cookbook Name:: mopidy-jukebox
# Recipe:: default

include_recipe 'build-essential::default'

%w{libsqlite3-dev libffi-dev gstreamer1.0-fluendo-mp3 gstreamer1.0-plugins-bad gstreamer1.0-alsa gstreamer1.0-plugins-good gstreamer1.0-plugins-ugly libssl-dev gir1.2-gstreamer-1.0 gir1.2-gst-plugins-base-1.0 python-dev python-gi cron git rsyslog}.each do |pkg|
	package pkg do
		action :install
	end
end

cookbook_file '/etc/logrotate.d/rsyslog' do
	source 'logrotate-rsyslog'
end

include_recipe "python::pip"

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

python_pip File.join(files_default, "requirements.txt") do
	options "--exists-action w -r"
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
	notifies :run, 'execute[reload systemd]', :immediately unless ENV['TEST_KITCHEN']
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
	action [:enable, :start] unless ENV['TEST_KITCHEN']
end

%w{luakit lxde-core lxsession lxlauncher nginx lightdm screen}.each do |pkg|
	package pkg do
		action :install
	end
end

service 'nginx' do
	provider Chef::Provider::Service::Systemd
	action [:enable, :start] unless ENV['TEST_KITCHEN']
end

cookbook_file "/etc/nginx/sites-available/default" do
	source "nginx.conf"
	owner "root"
	mode "0644"
	notifies :reload, 'service[nginx]', :immediately
end

directory '/home/pi/.config/luakit' do
	owner 'pi'
	mode '0755'
	action :create
	recursive true
end

file '/home/pi/.config/luakit/rc.lua' do
  content lazy { IO.read('/etc/xdg/luakit/rc.lua') }
  action :create_if_missing
end

ruby_block 'Edit Luakit config' do
	block do
		file = Chef::Util::FileEdit.new('/home/pi/.config/luakit/rc.lua')
		file.insert_line_if_no_match('/w.win.fullscreen/', \
	"for _, w in pairs(window.bywidget) do\n" \
	"	w.win.fullscreen = true\n"\
	"end\n")
		file.insert_line_if_no_match('/full_content_zoom/', \
	"webview.init_funcs.set_default_zoom = function (view, w)\n"\
		"	view.full_content_zoom = true -- optional\n"\
		"	view.zoom_level = 3 -- a 50% zoom\n"\
	"end\n")
		file.write_file
	end
	not_if {
		::File.readlines('/home/pi/.config/luakit/rc.lua').grep(/w.win.fullscreen/).any? and \
		::File.readlines('/home/pi/.config/luakit/rc.lua').grep(/full_content_zoom/).any?
	 }
end

ruby_block 'Edit Lightdm config' do
  block do
    file = Chef::Util::FileEdit.new('/etc/lightdm/lightdm.conf')
	  file.search_file_replace_line('/#autologin-user=/', 'autologin-user=pi')
    file.write_file
  end
	not_if { ::File.readlines('/etc/lightdm/lightdm.conf').grep(/autologin-user=pi/).any? }
end

service 'lightdm' do
	provider Chef::Provider::Service::Systemd
	action [:enable, :start] unless ENV['TEST_KITCHEN']
	subscribes :restart, 'ruby_block[Edit Lightdm config]', :immediately unless ENV['TEST_KITCHEN']
end

unless ENV['TEST_KITCHEN']
	execute 'dpms set' do
		command 'xset -dpms -display :0'
		user 'pi'
		action :run
	end

	execute 'screensaver off' do
		command 'xset -display :0 s off'
		user 'pi'
		action :run
	end

	execute 'luakit' do
		command 'screen -dmS luakit bash -c \'luakit http://jukebox/playlist-only.html\''
		environment 'DISPLAY' => ':0', 'HOME' => '/home/pi'
		user 'pi'
		not_if 'ls /var/run/screen/S-pi |grep luakit'
	end
end