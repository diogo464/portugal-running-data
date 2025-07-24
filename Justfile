_default:
    just --list

commit:
    ./commit-events.sh

scrape:
    ./fetch-sitemap
    ./setup-directories
    ./list-slugs | xargs -L 64 -P 40 ./fetch-page
    ./list-slugs | xargs -L 64 -P 0 ./extract-id
    ./list-slugs | xargs -L 64 -P 40 ./fetch-ics
    ./list-slugs | xargs -L 64 -P 40 ./fetch-data
    ./list-slugs | xargs -L 64 -P 40 ./fetch-image
    ./list-slugs | xargs -L 64 -P 40 ./fetch-location
    ./list-slugs | xargs -L 64 -P 20 ./fetch-oneline-description
    ./list-slugs | xargs -L 64 -P 40 ./extract-date
    ./list-slugs | xargs -L 64 -P 40 ./extract-categories
    ./list-slugs | xargs -L 64 -P 40 ./extract-circuits
    ./list-slugs | xargs -L 64 -P 40 ./extract-organizer
    ./list-slugs | xargs -L 64 -P 40 ./extract-slug
    ./list-slugs | xargs -L 64 -P 40 ./extract-title

scrape-categories:
    ./list-slugs | xargs -e -L 64 -P 1 ./extract-categories

scrape-circuits:
    ./list-slugs | xargs -e -L 64 -P 1 ./extract-circuits

scrape-organizer:
    ./list-slugs | xargs -e -L 64 -P 1 ./extract-organizer

