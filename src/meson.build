pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'constrict'
gnome = import('gnome')

gnome.compile_resources('constrict',
  'constrict.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'constrict.in',
  output: 'constrict',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'r-xr-xr-x'
)

constrict_sources = [
  '__init__.py',
  'main.py',
  'window.py',
  'constrict_utils.py',
  'enums.py',
  'sources_row.py',
  'sources_list_box.py',
  'shared.py',
  'error_dialog.py',
  'progress_pie.py',
  'preferences_dialog.py'
]

install_data(constrict_sources, install_dir: moduledir)
