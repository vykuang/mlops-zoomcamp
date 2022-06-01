import argparse
import requests
from pathlib import Path

def make_urls(taxi_type: int, start_month: int, end_month: int):
   
    if taxi_type == 1:    
        # green
        urls = [f'https://s3.amazonaws.com/nyc-tlc/trip+data/green_tripdata_2021-{i:02}.parquet'
               for i in range(start_month, end_month+1)]   
        
    elif taxi_type == 2:
        # for-hire vehicles
        urls = [f'https://nyc-tlc.s3.amazonaws.com/trip+data/fhv_tripdata_2021-{i:02}.parquet'
                for i in range(start_month, end_month+1)]
        
    else:
        return None
    
    return urls

def download_from_url(url: str, dest_path: str):
    """Wrapper function for requests library to stream download,
    i.e. without needing to store entire file in memory, and allows
    download to proceed in chunks

    Args:
    url: string
        direct url to the file for download, e.g.
        https://s3.amazonaws.com/nyc-tlc/trip+data/green_tripdata_2021-01.parquet

    file_dir: string
        path to the download destination directory
    """
    dest_path = Path(dest_path)
    if not dest_path.exists():
        Path.mkdir(dest_path)
        
    # choose url based on taxi type:
    

    # local_file = url.split('/')[-1].replace(" ", "_")
    # use built-in method to extract filename:
    local_file = Path(url).name
    local_path = Path(dest_path) / local_file

    if not local_path.exists():
        r = requests.get(url, stream=True)
        if r.ok:
            print('Saving to ', local_path)
            with open(local_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024*8):
                    # if chunk:
                    # iter_content will never return None type
                    f.write(chunk)
                    # f.flush()
                    # os.fsync(f.fileno())
        else:
            # HTTP status 4xx/5xx
            print(f'Download failed with code {r.status_code}\n{r.text}')
    else:
        print(f'File already exists:\n{local_path}')
        
        
if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--taxi_type', '-t',
        type=int,
        choices=range(1,3),
        required=True,
        help='Which taxi type to download data for: 1 for green, 2 for fhv',
    )
    parser.add_argument(
        '--dest_path', '-d',
        default='./output',
        help='Download directory for the fetched trip records',
    )
    parser.add_argument(
        '--start_month', '-s',
        type=int,
        choices=range(1,13),
        default=1,
        help='Int - Month in 2021 to start downloading',
    )
    parser.add_argument(
        '--end_month', '-e',
        type=int,
        choices=range(1,13),
        default=1,
        help='Int - Last month in 2021 to download data for',
    )
    args = parser.parse_args()
    
    urls = make_urls(args.taxi_type, args.start_month, args.end_month)
    for url in urls:
        download_from_url(url, args.dest_path)