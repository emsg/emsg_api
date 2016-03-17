#!/usr/bin/env bash
ps -ef |grep emsg_simple_api|awk '{print $2}'|xargs kill -9
rm -rf */*.pyc
rm -rf */*/*.pyc
uwsgi --http :6080 --socket :6088 --chdir `pwd` --module django_wsgi &
