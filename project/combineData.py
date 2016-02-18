import pandas as pd


def main():

    # Read in data
    releases = pd.read_csv('./data/release_dates.csv')
    ratings = pd.read_csv('./data/ratings.csv')
    writers = pd.read_csv('./data/writers.csv')

    # Get only those with season/episode info
    releases = releases[(releases.season.notnull()) & (releases.episode_num.notnull())]

    # Have to get row count down, limiting to US releases since 1990
    english_speaking_titles = releases[(releases.country == 'USA') & (releases.year > 1990)]
    print('There are {} english speaking titles with season/episode data.'.format(len(english_speaking_titles)))

    # This function is taken from how IMDB calculates raitings rank, helps to compare ones without any votes
    ratings['rank'] = (
        (ratings['votes'] / (ratings['votes'] + 25000)) * ratings['rating'] + (25000 / (ratings['votes'] + 25000))*6.9
                       )

    # Merge the datasets
    data = english_speaking_titles.merge(ratings, how='inner')
    data = data.merge(writers)

    print('Writing mainData.csv')
    data.to_csv('./data/mainData.csv', index=False)


if __name__ == '__main__':
    main()
