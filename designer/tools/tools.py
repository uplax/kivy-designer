import datetime
import os
import shutil
import sys

from designer.uix.confirmation_dialog import ConfirmationDialog
from designer.utils import constants
from designer.utils.utils import (
    get_current_project,
    get_designer,
    get_kd_data_dir,
    get_kd_dir,
    ignore_proj_watcher,
    show_alert,
)
from kivy.event import EventDispatcher
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup


#### UIs ####
class ToolSetupPy(BoxLayout):

    path = StringProperty('')
    '''setup.py path
       Instance of :class:`kivy.config.StringProperty`
    '''

    __events__ = ('on_create', 'on_cancel', )

    @ignore_proj_watcher
    def create(self):
        '''Create the setup.py
        '''
        package_name = self.ids.package_name.text
        version = self.ids.version.text
        url = self.ids.url.text
        license = self.ids.license.text
        author = self.ids.author.text
        author_email = self.ids.author_email.text
        description = self.ids.description.text

        setup_template = '''from distutils.core import setup

setup(
    name='%s',
    version='%s',
    packages=[],
    url='%s',
    license='%s',
    author='%s',
    author_email='%s',
    description='%s',
)
'''
        setup = setup_template % (
            package_name,
            version,
            url,
            license,
            author,
            author_email,
            description,
        )

        f = open(self.path, 'w').write(setup)

        self.dispatch('on_create')

    def on_create(self, *args):
        '''Event handler to "Create" button'''
        pass

    def on_cancel(self, *args):
        '''Event handler to "Cancel" button'''
        pass


### Tools ###
class DesignerTools(EventDispatcher):

    designer = ObjectProperty()
    '''Instance of Designer
       :data:`designer` is a :class:`~kivy.properties.ObjectProperty`
    '''

    @ignore_proj_watcher
    def export_png(self):
        '''Export playground widget to png file.
        If there is a selected widget, export it.
        If not, export the root widget
        '''
        playground = self.designer.ui_creator.playground
        proj_dir = get_current_project().path
        status = self.designer.statusbar

        wdg = playground.selected_widget
        if wdg is None:
            wdg = playground.root

        name = datetime.datetime.now().strftime("%m-%d-%Y_%H-%M-%S.png")
        if wdg.id:
            name = wdg.id + '_' + name
        wdg.export_to_png(os.path.join(proj_dir, name))
        status.show_message('Image saved at ' + name, 5, 'info')

    def check_pep8(self):
        '''Check the PEP8 from current project
        '''
        proj_dir = get_current_project().path
        kd_dir = get_kd_dir()
        pep8_dir = os.path.join(kd_dir, 'tools', 'pep8checker',
                                'pep8kivy.py')

        python_path =\
            self.designer.designer_settings.config_parser.getdefault(
                'global',
                'python_shell_path',
                ''
            )

        if python_path == '':
            self.profiler.dispatch('on_error', 'Python Shell Path not '
                                   'specified.'
                                   '\n\nUpdate it on \'File\' -> \'Settings\'')
            return

        if sys.platform[0] == 'w':
            pep8_dir = u'"' + pep8_dir + u'"'

        cmd = '%s %s %s' % (python_path, pep8_dir, proj_dir)
        self.designer.ui_creator.tab_pannel.switch_to(
            self.designer.ui_creator.tab_pannel.tab_list[2])
        self.designer.ui_creator.kivy_console.run_command(cmd)

    def create_setup_py(self):
        '''Runs the GUI to create a setup.py file
        '''
        d = get_designer()
        if d.popup:
            return False
        proj_dir = get_current_project().path
        designer_content = self.designer.designer_content

        setup_path = os.path.join(proj_dir, 'setup.py')
        if os.path.exists(setup_path):
            show_alert('Create setup.py', 'setup.py already exists!')
            return False

        content = ToolSetupPy(path=setup_path)
        d.popup = Popup(title='Create setup.py', content=content,
                        size_hint=(None, None), size=(550, 350),
                        auto_dismiss=False)
        content.bind(on_cancel=d.close_popup)

        def on_create(*args):
            designer_content.update_tree_view(get_current_project())
            d.close_popup()

        content.bind(on_create=on_create)
        d.popup.open()

    @ignore_proj_watcher
    def create_gitignore(self):
        '''Create .gitignore
        '''
        proj_dir = get_current_project().path
        status = self.designer.statusbar

        gitignore_path = os.path.join(proj_dir, '.gitignore')

        if os.path.exists(gitignore_path):
            show_alert('Create .gitignore', '.gitignore already exists!')
            return False

        gitignore = '''*.pyc
*.pyo
bin/
.designer/
.buildozer/
__pycache__/'''

        f = open(gitignore_path, 'w').write(gitignore)
        status.show_message('.gitignore created successfully', 5, 'info')

    def buildozer_init(self):
        '''Checks if the .spec exists or not; and when possible, calls
            _perform_buildozer_init
        '''
        d = get_designer()
        if d.popup:
            return False
        proj_dir = get_current_project().path
        spec_file = os.path.join(proj_dir, 'buildozer.spec')

        if os.path.exists(spec_file):
            confirm_dlg = ConfirmationDialog(
                message='The buildozer.spec file already exist.'
                        '\nDo you want to create a new spec?')
            d.popup = Popup(title='Buildozer init',
                            content=confirm_dlg,
                            size_hint=(None, None),
                            size=('250pt', '150pt'),
                            auto_dismiss=False)
            confirm_dlg.bind(on_ok=self._perform_buildozer_init,
                             on_cancel=d.close_popup)
            d.popup.open()
        else:
            self._perform_buildozer_init()

    @ignore_proj_watcher
    def _perform_buildozer_init(self, *args):
        '''Copies the spec from data/new_templates/default.spec to the project
        folder
        '''
        get_designer().close_popup()

        proj_dir = get_current_project().path
        spec_file = os.path.join(proj_dir, 'buildozer.spec')

        templates_dir = os.path.join(get_kd_data_dir(),
                                     constants.DIR_NEW_TEMPLATE)
        shutil.copy(os.path.join(templates_dir, 'default.spec'), spec_file)

        self.designer.designer_content.update_tree_view(get_current_project())
