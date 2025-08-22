project('constrict',
          version: '25.8.1',
    meson_version: '>= 1.0.0',
  default_options: [ 'warning_level=2', 'werror=false', ],
)

i18n = import('i18n')
gnome = import('gnome')

# Thank you to GNOME Music and Showtime... Their Meson configurations were
# useful to look at and 'borrow' from to set up my own Meson devel/release
# profiles.

if get_option('profile') == 'development'
  APPLICATION_ID = 'io.github.wartybix.Constrict.Devel'
  PREFIX = '/io/github/wartybix/Constrict/Devel'
else
  APPLICATION_ID = 'io.github.wartybix.Constrict'
  PREFIX = '/io/github/wartybix/Constrict'
endif

VCS_TAG = ''
if get_option('profile') != 'default'
  git = find_program('git', required : false)
  if git.found()
    VCS_TAG = run_command('git', 'rev-parse', '--short', 'HEAD', check: true).stdout().strip()
  endif
  if VCS_TAG == ''
    VCS_TAG = '-devel'
  else
    VCS_TAG = '-@0@'.format(VCS_TAG)
  endif
endif


subdir('data')
subdir('src')
subdir('po')

gnome.post_install(
     glib_compile_schemas: true,
    gtk_update_icon_cache: true,
  update_desktop_database: true,
)
