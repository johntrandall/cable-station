class CableStation < Formula
  include Language::Python::Virtualenv

  desc "Read USB-C cable e-markers, record each cable, and print a wrap-flag label"
  homepage "https://github.com/johntrandall/cable-station"
  url "https://github.com/johntrandall/cable-station/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "d508ef802242376a44a52f4a1d644109363a1b6d5456d7f6f9db543584cc6a1f"
  license "MIT"
  head "https://github.com/johntrandall/cable-station.git", branch: "main"

  depends_on "pillow" => :no_linkage
  depends_on "python@3.14"

  pypi_packages exclude_packages: "pillow"

  resource "linkify-it-py" do
    url "https://files.pythonhosted.org/packages/45/98/7a1a5f31fd5c7ba93e963b168e244b8e3dd705b3d2a718e3c3307583bf57/linkify_it_py-2.2.0.tar.gz"
    sha256 "d508ef802242376a44a52f4a1d644109363a1b6d5456d7f6f9db543584cc6a1f"
  end

  resource "markdown-it-py" do
    url "https://files.pythonhosted.org/packages/16/fc/cee2c45553c9a9bf77d8b0c391560c556d7ed756b1f0bb35eb5d48db09ea/markdown_it_py-4.3.0.tar.gz"
    sha256 "d508ef802242376a44a52f4a1d644109363a1b6d5456d7f6f9db543584cc6a1f"
  end

  resource "mdit-py-plugins" do
    url "https://files.pythonhosted.org/packages/ad/a4/77a4e1be19fd9b08993c76d5e54979ac836b327754f1f5fecfed1b56cc67/mdit_py_plugins-0.7.0.tar.gz"
    sha256 "d508ef802242376a44a52f4a1d644109363a1b6d5456d7f6f9db543584cc6a1f"
  end

  resource "mdurl" do
    url "https://files.pythonhosted.org/packages/d6/54/cfe61301667036ec958cb99bd3efefba235e65cdeb9c84d24a8293ba1d90/mdurl-0.1.2.tar.gz"
    sha256 "d508ef802242376a44a52f4a1d644109363a1b6d5456d7f6f9db543584cc6a1f"
  end

  resource "platformdirs" do
    url "https://files.pythonhosted.org/packages/d7/9a/8475be631fb33ca1466915e70fd594c42a4e84b512db650eaa14f90fe75d/platformdirs-4.14.5.tar.gz"
    sha256 "d508ef802242376a44a52f4a1d644109363a1b6d5456d7f6f9db543584cc6a1f"
  end

  resource "pygments" do
    url "https://files.pythonhosted.org/packages/49/2e/ced460408999b33da6b31b0021b0f37d329e202d4169aeb164493778f25b/pygments-2.21.0.tar.gz"
    sha256 "d508ef802242376a44a52f4a1d644109363a1b6d5456d7f6f9db543584cc6a1f"
  end

  resource "rich" do
    url "https://files.pythonhosted.org/packages/c0/8f/0722ca900cc807c13a6a0c696dacf35430f72e0ec571c4275d2371fca3e9/rich-15.0.0.tar.gz"
    sha256 "d508ef802242376a44a52f4a1d644109363a1b6d5456d7f6f9db543584cc6a1f"
  end

  resource "textual" do
    url "https://files.pythonhosted.org/packages/00/21/39a76b01bd5eea82a04baaca7580e105d8c59450df03998345bb2cfb307b/textual-8.2.8.tar.gz"
    sha256 "d508ef802242376a44a52f4a1d644109363a1b6d5456d7f6f9db543584cc6a1f"
  end

  resource "typing-extensions" do
    url "https://files.pythonhosted.org/packages/f6/cc/6253133b5bb138fc3306cebfbda2c520f545d36b5be2c7255cc528bb45d6/typing_extensions-4.16.0.tar.gz"
    sha256 "d508ef802242376a44a52f4a1d644109363a1b6d5456d7f6f9db543584cc6a1f"
  end

  def install
    virtualenv_install_with_resources
  end

  def caveats
    <<~EOS
      Optional tools: the tester path needs the `km003c` CLI (github.com/okhsunrog/km003c-rs);
      printing needs `ptouch-label` (uv tool install git+https://github.com/johntrandall/ptouch-label).
      `cable-station doctor` reports what it can see. Settings: ~/.config/cable-station/config.toml
    EOS
  end

  test do
    assert_match "cable-station 0.1.0", shell_output("#{bin}/cable-station --version")
    fixture = testpath/"capture.log"
    # a Discover Identity ACK from a passive 5 A, USB4 20G cable (the project's own test fixture)
    fixture.write <<~EOS
      [2815.575s] RAW[22]: 8F 51 41 A0 00 FF 00 00 00 18 00 00 00 00 00 00
                           00 00 42 40 08 00
      [2815.575s] SOP1: Data(VendorDefined)
    EOS
    assert_match "100W 5A", shell_output("#{bin}/cable-station decode #{fixture}")
    ENV["CABLE_STATION_DATA"] = testpath/"cables"
    ENV["CABLE_STATION_STATE"] = testpath/"state"
    ENV["CABLE_STATION_CONFIG"] = testpath/"none.toml"
    assert_match "km003c CLI", shell_output("#{bin}/cable-station doctor", 1)
  end
end
