#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Tests for parsing Meeting Minutes."""

import re

import shoki_config as cfg


def extract_blocks(text_minutes):
    """Separate the full minutes into individual topic blocks."""
    # The file starts with headers
    headers = True
    minutes_block = []
    prose_text = []
    new_topic = True
    for line in text_minutes.split('\n'):
        if line.strip() == '' and headers:
            # we are entering the topics.
            headers = False
        elif line.startswith(cfg.END):
            # we reached the end of the minutes section
            break
        elif not headers:
            # we are entering the minutes section
            if new_topic and line.startswith(cfg.TOPIC_HEADER):
                # a topic line starts a block
                new_topic = False
                text_block = {'topic_line': line}
                prose_text = []
            elif line.strip() != '':
                # if line is not empty it's part of a topic block.
                prose_text.append(line)
            elif not new_topic and line.strip() == '':
                # if line is empty we reached the end of a topic block.
                new_topic = True
                text_block['prose'] = prose_text
                minutes_block.append(text_block)
                text_block = {}
            else:
                # not an interesting line.
                continue
    return minutes_block


def extract_topic(topic_line):
    """Extract the topic and the owner of a discussion.

    - The first non empty line of a block.
    - Starting with a special character in config.
    - Return a dictionary with a topic and a owner.
    - Warns if there is no owner.
    """
    # we take the last parenthesis
    if '(' in topic_line:
        topic_text, owner_text = topic_line.rsplit('(', 1)
        # no space and remove the closing parenthesis
        owner = owner_text.strip()[:-1]
    else:
        topic_text = topic_line
        owner = None
    # we remove the starting characters and remove spaces
    topic = topic_text.split('#')[1].strip()
    return {'topic': topic, 'owner': owner}


def extract_prose(prose_block):
    """Extract a structure ready to be formatted.

    Input is a list of dictionaries, one for each topic.
    the dictionary
    """
    discussion = []
    speaking = False
    voice = {}
    description = {'intro': ''}
    for line in prose_block:
        speaker, sep, text = line.partition(':')
        if speaker.find(' ') == -1:
            # We are in the speaker section.
            speaking = True
            voice = {'speaker': speaker, 'said': text.lstrip()}
        else:
            # Either intro or continuation line.
            if not speaking:
                description['intro'] += '{} '.format(line)
            else:
                # this is a continuation line, we add the full line.
                voice['said'] += '{} '.format(line)
        if voice:
            discussion.append(voice)
    if description['intro']:
        discussion.append(description)
    return discussion


def meta_headers(text_minutes):
    """Extract the metadata section of a meeting.

    - simple format of Key: Value.
    - Ends with a blank line.
    - Returns a dictionary.
    """
    meta = {}
    for line in text_minutes.split('\n'):
        if line.strip() == '':
            break
        meta_key, meta_value = line.split(':', 1)
        meta[meta_key.strip().lower()] = meta_value.strip()
    return meta


def meeting_date(meta_date):
    """Extract the meeting date.

    parses a date with the format 21 March 2017 and returns 2017-03-21."""
    pattern = re.compile(('(?P<day>\d{1,2})\s+'
                          '(?P<month>\w+)\s+'
                          '(?P<year>\d{4})[\s-]*'
                          '(?P<time>\d{1,2}:\d{1,2})\s+'
                          '(?P<timezone>\w+)'))
    result = pattern.search(meta_date)
    day = result.group('day')
    month = result.group('month')
    year = result.group('year')
    time = result.group('time')
    timezone = result.group('timezone')
    if month == 'March':
        month = '03'
    return '{0}-{1}-{2}'.format(year, month, day)
