# LIFT Homebrew Formula
# This formula will be auto-updated by the release workflow

class Lift < Formula
  include Language::Python::Virtualenv

  desc "Bodybuilding workout tracker CLI"
  homepage "https://github.com/parkerdgabel/lift"
  url "https://github.com/parkerdgabel/lift/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "" # This will be filled by the release workflow
  license "MIT"

  depends_on "python@3.11"

  resource "typer" do
    url "https://files.pythonhosted.org/packages/typer/typer-0.12.0.tar.gz"
    sha256 ""
  end

  resource "rich" do
    url "https://files.pythonhosted.org/packages/rich/rich-13.7.0.tar.gz"
    sha256 ""
  end

  resource "duckdb" do
    url "https://files.pythonhosted.org/packages/duckdb/duckdb-1.0.0.tar.gz"
    sha256 ""
  end

  resource "pydantic" do
    url "https://files.pythonhosted.org/packages/pydantic/pydantic-2.8.0.tar.gz"
    sha256 ""
  end

  resource "plotext" do
    url "https://files.pythonhosted.org/packages/plotext/plotext-5.2.8.tar.gz"
    sha256 ""
  end

  resource "python-dateutil" do
    url "https://files.pythonhosted.org/packages/python-dateutil/python-dateutil-2.9.0.tar.gz"
    sha256 ""
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/lift", "version"
  end
end
