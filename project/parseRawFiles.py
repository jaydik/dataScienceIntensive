"""Build the tutorial data files from the IMDB *.list.gz files."""

import csv
import gzip
import os
import re
from datetime import datetime

split_on_tabs = re.compile(b'\t+').split


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    if not os.path.isdir('./data'):
        os.makedirs('./data')

    # Load movie titles.

    titles = set()
    uninteresting_titles = set()

    lines = iter(gzip.open('./data/genres.list.gz'))
    line = next(lines)
    while line != b'8: THE GENRES LIST\n':
        line = next(lines)
    assert next(lines) == b'==================\n'
    assert next(lines) == b'\n'

    print('Reading "genres.list.gz" to find interesting movies')

    for line in lines:
        if not_a_real_tv_show(line):
            continue

        fields = split_on_tabs(line.strip(b'\n'))
        raw_title = fields[0]
        genre = fields[1]

        try:
            raw_title.decode('ascii')
        except UnicodeDecodeError:
            continue

        if genre in (b'Adult', b'Documentary', b'Short'):
            uninteresting_titles.add(raw_title)
        else:
            titles.add(raw_title)

    interesting_titles = titles - uninteresting_titles
    del titles
    del uninteresting_titles

    print('Found {0} titles'.format(len(interesting_titles)))

    print('Writing "titles.csv"')

    with open('./data/titles.csv', 'w') as f:
        output = csv.writer(f)
        output.writerow(('title', 'year', 'episode_name', 'season', 'episode_num'))
        for raw_title in interesting_titles:
            title, year, episode_name, season, episode_num = parse_title(raw_title)
            output.writerow([title, year, episode_name, season, episode_num])

    print('Finished writing "titles.csv"')
    print('Reading release dates from "release-dates.list.gz"')

    lines = iter(gzip.open('data/release-dates.list.gz'))
    line = next(lines)
    while line != b'RELEASE DATES LIST\n':
        line = next(lines)
    assert next(lines) == b'==================\n'

    output = csv.writer(open('./data/release_dates.csv', 'w'))
    output.writerow(('title', 'year', 'episode_name', 'season', 'episode_num', 'country', 'date'))

    for line in lines:
        if not_a_real_tv_show(line):
            continue

        if line.startswith(b'----'):
            continue

        fields = split_on_tabs(line.strip(b'\n'))
        if len(fields) > 2:     # ignore "DVD premier" lines and so forth
            continue

        raw_title = fields[0]
        if raw_title.split(b'{')[0].strip() not in interesting_titles:
            continue

        title, year, episode_name, season, episode_num = parse_title(raw_title)
        if title is None:
            continue

        country, datestr = fields[1].decode('ascii').split(':')
        try:
            date = datetime.strptime(datestr, '%d %B %Y').date()
        except ValueError:
            continue  # incomplete dates like "April 2014"
        output.writerow((title, year, episode_name, season, episode_num, country, date))

    print('Finished writing "release_dates.csv"')

    print('Reading writers from "writers.list.gz"')
    output = csv.writer(open('./data/writers.csv', 'w'))
    output.writerow(('title', 'year', 'episode_name', 'season', 'episode_num', 'name', 'type'))

    lines = iter(gzip.open('./data/writers.list.gz'))

    line = next(lines)
    while (b'Name' not in line) or (b'Titles' not in line):
        line = next(lines)

    assert b'----' in next(lines)

    name = ''
    for line in lines:
        if line.startswith(b'----------------------'):
            break

        line = line.rstrip()
        if not line:
            continue

        fields = split_on_tabs(line.strip(b'\n'))
        if fields[0]:
            name = decode_ascii(fields[0])
            name = swap_names(name)

        if not_a_real_tv_show(fields[1]):
            continue

        raw_title = fields[1].split(b'  ')[0]
        extra_crap = fields[1].split(b'  ')[1:]
        if raw_title.split(b'{')[0].strip() not in interesting_titles:
            continue

        title, year, episode_name, season, episode_num = parse_title(raw_title)

        if title is None:
            continue

        writer_type = ''
        for crap in extra_crap:
            if re.match(b'\(\d{4}\)', crap):
                continue
            if re.match(b'<\d+,\d+,\d+>', crap):
                continue
            if b'as' in crap:
                continue
            if re.search(b'(\w+)\s+"[^"]+"', crap):
                writer_type = re.search(b'(\w+) "[^"]+"', crap).group(1).decode('latin-1')
                break
            if re.search(b'(\w+)\)\s+\([^\)]+', crap):
                writer_type = re.search(b'(\w+)\)\s+\([^\)]+', crap).group(1).decode('latin-1')
                break

            writer_type = crap.strip(b'()').decode('latin-1')

        output.writerow((title, year, episode_name, season, episode_num, name, writer_type))

    print('Finished writing "writers.csv"')

    print('Reading ratings from "ratings.list.gz"')

    lines = iter(gzip.open('data/ratings.list.gz'))
    output = csv.writer(open('./data/ratings.csv', 'w'))
    output.writerow(('title', 'year', 'episode_name', 'season', 'episode_num', 'rating', 'votes'))

    line = next(lines)
    while line != b'MOVIE RATINGS REPORT\n':
        line = next(lines)

    next(lines)
    assert next(lines) == b'New  Distribution  Votes  Rank  Title\n'

    ratings_pattern = re.compile(b'[0-9\.\*]{10}\s+(?P<votes>\d+)\s+(?P<rating>\d+\.\d+)\s+(?P<title>.*)$')
    for line in lines:
        if line.startswith(b'\n'):
            break

        matches = ratings_pattern.search(line).groupdict()

        if matches['title'].split(b'{')[0].strip() not in interesting_titles:
            continue
        title, year, episode_name, season, episode_num = parse_title(matches['title'])

        output.writerow((title,
                         year,
                         episode_name,
                         season,
                         episode_num,
                         float(matches['rating']),
                         int(matches['votes'])))


def not_a_real_tv_show(line):
    return (
        b'"' not in line or
        b'{{SUSPENDED}}' in line or        # Suspended
        b' (????' in line or               # Unknown year
        b' (TV)' in line or                # TV Movie
        b' (V)' in line or                 # Video
        b' (VG)' in line                   # Video game
        )


match_title_full = re.compile(r'^(.*)\s+\((\d+)(/[IVXL]+)?\)\s+\{([^}]+)(\(#(\d+)\.(\d+)\))\}$').match
match_title_no_ep = re.compile(r'^(.*)\s+\((\d+)(/[IVXL]+)?\)\s+\{(\(?[^}(]+)?(\(Pilot\))?\}$').match
match_title_no_tit = re.compile(r'^(.*)\s+\((\d+)(/[IVXL]+)?\)\s+\{\(#(\d+)\.(\d+)\)\}$').match
match_title_series = re.compile(r'^(.*)\s+\((\d+)(/[IVXL]+)?\)$').match


def parse_title(raw_title):
    try:
        title = raw_title.decode('ascii')
    except UnicodeDecodeError:
        return None, None, None, None, None

    m = match_title_full(title)
    n = match_title_no_ep(title)
    o = match_title_no_tit(title)
    p = match_title_series(title)

    if m:
        title = m.group(1)
        year = int(m.group(2))
        numeral = m.group(3)
        episode_name = m.group(4)
        season = m.group(6)
        episode_num = m.group(7)
    elif n:
        title = n.group(1)
        year = int(n.group(2))
        numeral = n.group(3)
        episode_name = n.group(4)
        season = ''
        episode_num = ''
    elif o:
        title = o.group(1)
        year = int(o.group(2))
        numeral = o.group(3)
        episode_name = ''
        season = o.group(4)
        episode_num = o.group(5)
    elif p:
        title = p.group(1)
        year = int(p.group(2))
        numeral = p.group(3)
        episode_name = ''
        season = ''
        episode_num = ''
    else:
        print("done goof'd on " + title)
        return None, None, None, None, None

    if numeral is not None:
        numeral = numeral.strip('/')
        if numeral != 'I':
            title = '{0} ({1})'.format(title, numeral)

    return title, year, episode_name, season, episode_num


def swap_names(name):
    if name.endswith(' (I)'):
        name = name[:-4]
    if ',' in name:
        last, first = name.split(',', 1)
        name = first.strip() + ' ' + last.strip()
    return name


def decode_ascii(s):
    return s.decode('ascii', 'replace').replace(u'\ufffd', u'?')


if __name__ == '__main__':
    main()
