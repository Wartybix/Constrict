pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'constrict'
gnome = import('gnome')

gresource_conf = configuration_data()
gresource_conf.set('PREFIX', PREFIX)

blueprints = custom_target('blueprints',
  input: files(
    'attempt_fail_box.blp',
    'error_dialog.blp',
    'sources_list_box.blp',
    'progress_popover_box.blp',
    'preferences_dialog.blp',
    'gtk/shortcuts-dialog.blp',
    'window.blp',
    'sources_row.blp',
    'current_attempt_box.blp'
  ),
  output: '.',
  command: [find_program('blueprint-compiler'), 'batch-compile', '@OUTPUT@', '@CURRENT_SOURCE_DIR@', '@INPUT@'],
)

gnome.compile_resources(
  'constrict',
  configure_file(
    input: 'constrict.gresource.xml.in',
    output: 'constrict.gresource.xml',
    configuration: gresource_conf
  ),
  gresource_bundle: true,
  dependencies: blueprints,
  install: true,
  install_dir: pkgdatadir,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version() + VCS_TAG)
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)
conf.set('APPLICATION_ID', APPLICATION_ID)
conf.set('PREFIX', PREFIX)

configure_file(
  input: 'constrict.in',
  output: 'constrict',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'r-xr-xr-x'
)

constrict_sources = [
  # '__init__.py',
  configure_file(
    input: '__init__.py.in',
    output: '__init__.py',
    configuration: conf
  ),
  'main.py',
  'window.py',
  'constrict_utils.py',
  'enums.py',
  'sources_row.py',
  'sources_list_box.py',
  'shared.py',
  'error_dialog.py',
  'progress_pie.py',
  'preferences_dialog.py',
  'attempt_fail_box.py',
  'progress_popover_box.py',
  'current_attempt_box.py'
]

install_data(constrict_sources, install_dir: moduledir)
