from flask import Flask, render_template, request, send_file
import openeo
import xarray
import rioxarray
import matplotlib.pyplot as plt
import os
from datetime import datetime
from tqdm import tqdm

# 非インタラクティブモードに設定
import matplotlib

matplotlib.use("Agg")

app = Flask(__name__)

# ======================
# CDESのバックエンドと接続とOIDC認証
# ======================
connection = openeo.connect("openeo.dataspace.copernicus.eu")
connection.authenticate_oidc()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/process", methods=["POST"])
def process():
    west = float(request.form["west"])
    south = float(request.form["south"])
    east = float(request.form["east"])
    north = float(request.form["north"])

    # datacubeの設定
    datacube = connection.load_collection(
        "SENTINEL2_L2A",
        spatial_extent={
            "west": west,
            "south": south,
            "east": east,
            "north": north,
            "crs": "EPSG:4326",
        },
        temporal_extent=["2022-03-01", "2024-03-31"],
        bands=["B04", "B03", "B02", "SCL"],
        max_cloud_cover=20,
    )

    # 現在の日時を取得してファイル名を生成
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"s2_{current_time}.nc"

    # ファイルの存在を確認して、存在しない場合のみダウンロード
    if not os.path.exists(filename):
        print(f"{filename} が存在しません。ダウンロードを開始します。")
        # download_with_progress(datacube, filename)
        datacube.download(filename)
    else:
        print(f"{filename} はすでに存在します。")

    # 保存したncデータをxarrayとして読み込む
    ds = xarray.open_dataset(filename)
    rgb_data = ds[["B04", "B03", "B02"]].isel(t=0).to_array(dim="bands")

    output_image = f"static/rgb_{current_time}.png"

    # staticディレクトリが存在しない場合は作成
    if not os.path.exists("static"):
        os.makedirs("static")

    # 手動でプロットを作成
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.imshow(rgb_data.transpose("y", "x", "bands").values / 10000.0)  # 正規化して表示
    plt.axis("off")
    plt.savefig(output_image, bbox_inches="tight", pad_inches=0)
    plt.close(fig)

    # 使用した.ncファイルを削除
    os.remove(filename)

    # 画像のパスと地理的境界を返す
    return render_template(
        "index.html",
        image_url=output_image,
        west=west,
        south=south,
        east=east,
        north=north,
    )


if __name__ == "__main__":
    app.run(debug=True)
