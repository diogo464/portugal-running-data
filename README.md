# portugal-running-data
repo with scraper for the portugal running calendar data

| Filename                                                      | Source Script                                                 | Optional                                                      | Description                                                   |
| ------------------------------------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------- |
| `lastmod`                                                     | `setup-directories`                                           | no                                                            | last modification time extracted from the sitemap file        |
| `page.html`                                                   | `fetch-page`                                                  | no                                                            | event page from portugalrunning.com                           |
| `id`                                                          | `extract-id`                                                  | no                                                            | event numeric id from wordpress                               |
| `data.json`                                                   | `fetch-data`                                                  | no                                                            | json file with some event data                                |
| `ics`                                                         | `fetch-ics`                                                   | no                                                            | calendar file with location, date and other event information |
| `location`                                                    | `fetch-location`                                              | yes                                                           | location data for the event                                   |
| `image`                                                       | `fetch-image`                                                 | yes                                                           | cover image for the event                                     |
| `date`                                                        | `extract-date`                                                | no                                                            | event date extracted from the ics file                        |
| `oneline-description`                                         | `fetch-oneline-description`                                   | yes                                                           | ai generated one line description                             |
| `categories`                                                  | `extract-categories`                                          | no                                                            | event categories                                              |
| `circuits`                                                    | `extract-circuits`                                            | no                                                            | event circuits                                                |

## `fetch-sitemap`
this script fetches the sitemap that contains a list of event page urls and the last modification date

## `fetch-pages`
this script will fetch any missing pages or outdated pages by looking at the lastmod file.

## `extract-ids`
this script will extract the event ids from the page.html file. this id can be used to later fetch other data related to this event.

## `fetch-ics`
this script uses the event id and fetches its ics file.

## `fetch-data`
this script uses the event id to fetch some event data in json format.

## `fetch-images`
some events have a main image in the json data file, this script will fetch that image.

## `extract-organizer`
this script extracts the organizer from the class list in the json data file, if one exists.

## `extract-categories`
this script extracts a list of categories from the class list in the json data file.
