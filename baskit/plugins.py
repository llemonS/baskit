import cmd
import os
import config
import shutil
from bukget import api
from hashlib import md5
from ConfigParser import ConfigParser
from zipfile import ZipFile 
from StringIO import StringIO

class Plugins(cmd.Cmd):
    def __init__(self, server):
        overrides = {
            'spigot': 'bukkit',
        }
        cmd.Cmd.__init__(self)
        self.server = server
        self.plugin_path = os.path.join(self.server.env, 'env', 'plugins')
        if server.server_type in overrides:
            self.stype = overrides[server.server_type]
        else:
            self.stype = server.server_type


    def get_plugin(self, name):
        '''
        Returns a dictionary with the plugin information.
        '''
        stanza = 'Plugin: %s' % name.lower()
        conf = ConfigParser()
        conf.read(config.get_config_file())
        if config.has_section(stanza):
            return {
                'name': conf.get(stanza, 'name'),
                'jar': conf.get(stanza, 'jar'),
                'bukget': conf.get(stanza, 'bukget'),
                'md5': conf.get(stanza, 'md5'),
                'version': conf.get(stanza, 'version'),
                'enabled': conf.getboolean(stanza, 'enabled'),
            }
        else:
            return None


    def plugin_listing(self):
        '''
        Returns a list of dictionaries with the installed plugins that baskit
        is aware of.
        '''
        conf = ConfigParser()
        conf.read(config.get_config_file())
        plugins = []
        for section in conf.sections():
            if 'Plugin:' in section:
                plugins.append(self.get_plugin(conf.get(section, 'name')))
        return plugins


    def save_plugin(self, name, **settings):
        '''
        Saves any changes to the config file.
        '''
        stanza = 'Plugin: %s' % name.lower()
        conf = ConfigParser()
        conf.read(config.get_config_file())
        settings['name'] = name
        for item in settings:
            conf.set(stanza, setting, settings[setting])
        with open(config.get_config_file(), 'w') as cfile:
            conf.write(cfile)


    def get_plugin_info(self, filename):
        '''
        Will get the main & version information from the plugin and will
        query BukGet to look for a match.  If we do find a match we will add
        the plugin to your list of managed plugins within baskit.
        '''
        return bukget.orm.search({
            'field': 'versions.md5', 
            'action': '=',
            'value': self.hash_file(filename)
        })


    def hash_file(self, filename):
        '''
        Returns the md5sum of a file.
        '''
        dataobj = open(filename)
        md5hash = md5()
        md5hash.update(dataobj.read())
        dataobj.close()
        return md5hash.hexdigest()


    def display_plugin(self, plugin, *opts):
        '''
        Outputs to Screen information about the plugin.
        '''
        conf = get_plugin(plugin)
        ret = api.plugin_details(self.stype, conf['slug'])
        if ret is not None:
            current = ret['versions'][0]
            for version in ret['versions']:
                if conf['version'] == version['version']:
                    if current['date'] > version['date']:
                        opts.append('Current: %s' % current['version'])
        print '%-20s %-10s %s' % (conf['name'], conf['version'], ', '.join(opts))


    def install(plugin, version):
        '''
        Installs or Updates a Plugin.
        '''
        plug = api.plugin_details(self.stype, plugin, version)
        


    def do_help(self, s):
        if s == '': self.onecmd('help help')
        else:
            cmd.Cmd.do_help(self, s) 


    def help_help(self):
        print '''Plugin Management Functions 

        Info will eventually go here.....
        '''
    

    def do_scan(self, s):
        '''scan
        Scans the currently installed plugins and will add any not currently
        being tracked into the baskit config as well as update any version
        numbers for plugins that have been updated manually.
        '''
        plugins = self.plugin_listing()
        for filename in os.listdir(self.plugin_path):
            filepath = os.path.join(self.plugin_path, filename)
            if 'jar' == filename[-3:].lower():
                p = False
                for plugin in plugins:
                    if plugin['jar'] == filename:
                        p = plugin
                if p:
                    plug = api.plugin_details(self.stype, p['slug'])
                else:
                    plugs = self.get_plugin_info(filepath)
                    if len(plugs) == 0:
                        print 'Plugin %s does not exist in BukGet.' % filename
                        continue
                    elif len(plugs) == 1:
                        plug = plugs[0]
                    if len(plugs) > 1:
                        print 'Multiple Matches for %s.  Please Select One (default 0)' % filename
                        for item in plugs:
                            print '%2d: %-30s %s' % (plugs.index(item),
                                                     item['plugin_name'],
                                                     item['slug'])
                        try:
                            plug = plugs[int(raw_input('Plugin ID : '))]
                        except ValueError:
                            plug = plugs[0]
                filehash = self.hash_file(filepath)
                notes = []
                for version in plug['versions']:
                    if version['md5'] == filehash:
                        self.save_plugin(plug['plugin_name'].lower(),
                            jar=filename,
                            bukget=plug['slug'],
                            md5=filehash,
                            version=version['version'],
                            enabled=True)
                        if p and p['md5'] != version['md5']:
                            notes.append('Manually Updated')
                self.display_plugin(plug['plugin_name'].lower(), *notes)


    def do_search(self, s):
        '''search [search_string]
        Searches for a given plugin name.
        '''
        results = api.search({
            'field': 'plugin_name', 
            'action': 'like',
            'value': s
        })
        print '\n'.join(['%-15s %-15s %s' % (p['plugin_name'], p['slug'], p['description']) for p in results])


    def do_list(self, s):
        '''list 
        Lists the currently installed plugins and their versions.  Will also 
        note which plugins have updates available.
        '''
        for plugin in self.plugin_listing():
            self.display_plugin(plugin)


    def do_update(self, s):
        '''update [plugin_name|all] [version]
        Will update a singular plugin (or all plugins if specified) to either
        current or the version specified
        '''
        dset = s.split()
        plugin = None
        version = 'latest'
        if len(dset) > 0: plugin = dset[0].lower()
        if len(dset) > 1: version = dset[1]
        if plugin:
            if plugin == 'all':
                for plug in self.plugin_listing():
                    self.install(plug['name'], version)
            else:
                self.install(plugin, version)
        else:
            print 'No Options Defined!'
    

    def do_install(self, s):
        '''install [plugin_name] [version]
        Installs either the latest version, or the version specified.
        '''
        dset = s.split()
        plugin = None
        version = 'latest'
        if len(dset) > 0: plugin = dset[0].lower()
        if len(dset) > 1: version = dset[1]
        if plugin:
            self.install(plugin, version)
    

    def do_remove(self, s):
        '''remove [plugin_name]
        Removes the specified plugin binary.  Please note that as many plugins
        will create data structures themselves, removing the plugin binary will
        NOT necessarially remove all fo the associated configuration and data 
        files.
        '''
        if self.server.running():
            print 'Please shutdown the server before permanently removing plugins.'
            return
        paths = []
        if raw_input('Delete %s ? (NO/yes)').lower() in ['y', 'yes']:
            pass
        pass
    

    def do_enable(self, s):
        '''enable [plugin_name]
        Enables a disabled plugin.  This will simply move the plugin binary back
        into the plugin folder, effectively enabling the plugin.
        '''
        plugin = self.get_plugin(s)
        if os.path.exists(os.path.join('%s_disabled' % self.plugins_path, plugin[1])):
            shutil.move(os.path.join('%s_disabled' % self.plugins_path, plugin[1]), 
                        os.path.join(self.plugins_path, plugin[1]))
            print '%s enabled.  Restart the servert to activate.' % plugin[0]
        else:
            print '%s is not disabled.' % plugin[0]


    def do_disable(self, s):
        '''disable [plugin_name]
        Disables a plugin.  This will move the plugin binary (not any of the 
        associated data) into the disabled-plugins folder.  This is designed to
        be a non-destructive way to troubleshoot potential issues.
        '''
        plugin = self.get_plugin(s)
        if not os.path.exists('%s_disabled' % self.plugins_path):
            os.makedirs('%s_disabled' % self.plugins_path)
        if os.path.exists(os.path.join(self.plugins_path, plugin[1])):
            shutil.move(os.path.join(self.plugins_path, plugin[1]), 
                        os.path.join('%s_disabled' % self.plugins_path, plugin[1]))
            print '%s disabled.  Restart the server to deactivate.' % plugin[0]
        else:
            print '%s is not installed.' % plugin[0]