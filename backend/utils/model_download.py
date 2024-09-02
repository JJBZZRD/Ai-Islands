import argparse

from backend.controlers.model_control import ModelControl


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="ModelDownload",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="This script downloads the model with the given model_id",
        epilog="""
This script is mirror of the download method in the ModelControl class. 
The purpose of this script is to allow model downloaded in a new terminal, so that the user can monitor the download progress.
""",
    )
    parser.add_argument('model_id', type=str, help="The model_id of the model to download")
    parser.add_argument('-at', '--auth_token', type=str, help="The auth token for model download")
    
    args = parser.parse_args()
    
    model_control = ModelControl()
    model_control._download_model(args.model_id, args.auth_token)
    print("=====model download complete=====")
