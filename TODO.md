# TODO

 - configure alternatives to ``uwsgi``
 - avoid ``tr: write error: Broken pipe`` from ``hooks/post_gen_project.sh``
 - manage TSL certificates (otherwise nginx wouldn't start)
 - generate ``env`` file
 - generate ``uwsgi.ini`` file
 - print a message at the end of the creation telling the user of copying some file
   into the main repo (mainly ``uwsgi.ini``).
 - make locale configurable.
 - choose between ``site_name`` and ``project_name`` as naming variable.
