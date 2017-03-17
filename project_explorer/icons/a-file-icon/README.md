# [![A File Icon][img-logo]][downloads]

[![Star on GitHub][img-stars]][stars]
[![Make a donation at Patreon][img-patreon]][patreon]
[![Share via Twitter][img-twitter]][twitter]
[![Join the chat at Gitter][img-gitter]][gitter]
[![Join the chat at Sublime Forum][img-forum]][forum]

This package adds file-specific icons to Sublime Text for improved visual grepping. It's heavily inspired by [Atom File Icons][atom-file-icons].

Its aims are:

* To be a `tmPreferences` storage for UI themes those support file-specific icons.
* To provide icons for themes those don't (fully) support file-specific icons.

If you have any problems, please search for a similar issue first, before creating [a new one][new-issue]. 

> Also, check the list of [known issues][known-issues] before doing so.

## Users

### Getting Started

[![Getting Started with A File Icon][img-getting-started]][getting-started]

### Installation

#### Package Control

The easiest way to install is using Sublime's [Package Control][downloads]. It's listed as `A File Icon`.

1. Open `Command Palette` using menu item `Tools → Command Palette...`
2. Choose `Package Control: Install Package`
3. Find `A File Icon` and hit `Enter`

#### Download

1. [Download the `.zip`][release]
2. Unzip and rename folder to `A File Icon`
3. Copy folder into `Packages` directory, which you can find using the menu item `Preferences → Browse Packages...`

> **Note:** Don't forget to restart Sublime Text after installing this package. 

### Customization

You can change the color, opacity level and size of the icons by modifying your user preferences file, which you can find by:

* `Preferences → Package Settings → A File Icon → Settings`,
* Choose `A File Icon: Settings` in `Command Palette`.

### Wrong Icons

Sublime Text uses syntax scopes for file-specific icons. That's why icons of packages provided by the community require them to be installed.

See the list of [community packages][packages] that you may need to install to see the right icon.

### Themes

If your theme supports an icon customization you can choose what icons you want to use – provided by the theme (by default) or provided by the package. Otherwise this package adds its own icons only.

Themes that already have support of the icon customization include:

* [Boxy Theme][boxy-theme]
* [Material Theme][material-theme]

### Troubleshooting

If something goes wrong try to:

1. Open `Command Palette` using menu item `Tools → Command Palette...`.
2. Choose `A File Icon: Clean Patches`.
3. Restart Sublime Text.

## Developers

### Bring Support of the File Icon Customization to Your Theme

If you are a theme developer and you want to support a file icon customization, you should:

* Remove all stuff related to the icon setup: `.tmPreferences`, `.sublime-settings`, `.sublime-syntax` and `.tmLanguage` files.
* Rename all your existing icons to match [these ones][icons].
* Add `.supports-a-file-icon-customization` file to the root of your theme (this is how we check if the theme **supports** customization of the file-specific icons).
* Also you can provide [this script][installer] which recommends user to install `A File Icon` for enhanced support of the file-specific icons.

### How It Works

In simple terms, `A File Icon` does the following:

1. Copies all the necessary files right after install or upgrade to `zzz A File Icon zzz` directory
2. Searches all installed themes
3. Checks if themes are already patched, if not
4. Patches them by generating `<theme-name>.sublime-theme` files from a [template][template]
5. For themes those support file icon customization, it provides `.tmPreferences` files and missing icons by default (user can override icons provided by the theme via `"force_mode": true`).

The real process is just a little bit more complex to minimize hard drive I/O.

### Contributing

Want to contribute some code? Excellent! Read up on our [guidelines][contributing].

## Resources

### Colors

Colors are from the [Boxy Theme][boxy-theme] icon color palette. They are bright because they should look good with most themes. However you can change color and opacity level of all icons. See [customization][customization].

![Palette][img-palette]

### Icons

This package contains icons provided by:

- [Atom File Icons][atom-file-icons]
- [Boxy Theme][boxy-theme]
- [Devicons][devicons]
- [Font Awesome][font-awesome]
- [Font Mfizz][font-mfizz]
- [Icomoon][icomoon]
- [Octicons][octicons]

Source icons are provided in SVG format (Sublime Text doesn't currently support it). We convert them to @1x, @2x and @3x PNG assets before each release via a custom `gulp` task. 

Rasterized icons can be found in `icons` folder.

## Share The Love

I've put a lot of time and effort into making **A File Icon** awesome. If you love it, you can buy me a coffee. I promise it will be a good investment 😉.

**Donate with:** [Patreon][patreon].

<!-- Resources -->

[atom-file-icons]: https://github.com/file-icons/atom
[boxy-theme]: https://github.com/ihodev/sublime-boxy
[devicons]: http://vorillaz.github.io/devicons/#/main
[font-awesome]: http://fontawesome.io/
[font-mfizz]: http://fizzed.com/oss/font-mfizz
[icomoon]: https://icomoon.io/
[material-theme]: https://github.com/equinusocio/material-theme
[octicons]: https://octicons.github.com/

<!-- Misc -->

[changelog]: https://github.com/ihodev/a-file-icon/blob/dev/CHANGELOG.md
[coming-soon]: https://github.com/wbond/package_control_channel/pull/6109
[contributing]: https://github.com/ihodev/a-file-icon/blob/dev/.github/CONTRIBUTING.md
[customization]: https://github.com/ihodev/a-file-icon#customization
[downloads]: https://packagecontrol.io/packages/A%20File%20Icon 'A File Icon @ Package Control'
[forum]: https://forum.sublimetext.com/t/a-file-icon-sublime-file-specific-icons-for-improved-visual-grepping/25874
[getting-started]: https://youtu.be/aTpuEhVHASw 'Watch "Getting Started with A File Icon" on YouTube'
[gitter]: https://gitter.im/a-file-icon/Lobby
[icons]: https://github.com/ihodev/a-file-icon/tree/dev/icons/multi
[installer]: https://github.com/ihodev/sublime-boxy/blob/dev/Icons.py
[known-issues]: https://github.com/ihodev/a-file-icon/labels/known%20issue
[new-issue]: https://github.com/ihodev/a-file-icon/issues/new
[packages]: https://github.com/ihodev/a-file-icon/blob/dev/PACKAGES.md
[patreon]: https://www.patreon.com/ihodev
[release]: https://github.com/ihodev/a-file-icon/releases
[stars]: https://github.com/ihodev/a-file-icon/stargazers
[template]: https://github.com/ihodev/a-file-icon/blob/dev/common/templates/theme.py
[issues]: https://github.com/ihodev/a-file-icon/issues
[twitter]: https://twitter.com/intent/tweet?hashtags=sublimetext%2C%20file%2C%20icons&ref_src=twsrc%5Etfw&text=A%20File%20Icon%20%E2%80%93%20Sublime%20file%20icons%20for%20improved%20visual%20grepping%20%F0%9F%8E%89&tw_p=tweetbutton&url=https%3A%2F%2Fgithub.com%2Fihodev%2Fa-file-icon&via=ihodev

<!-- Assets -->

[img-forum]: https://cdn.rawgit.com/ihodev/a-file-icon/dev/media/reply-on-forum.svg
[img-getting-started]: https://cdn.rawgit.com/ihodev/a-file-icon/dev/media/getting-started.jpg
[img-gitter]: https://cdn.rawgit.com/ihodev/a-file-icon/dev/media/chat-on-gitter.svg
[img-logo]: https://cdn.rawgit.com/ihodev/a-file-icon/dev/media/logo.png
[img-palette]: https://cdn.rawgit.com/ihodev/a-file-icon/dev/media/palette.png
[img-patreon]: https://cdn.rawgit.com/ihodev/a-file-icon/dev/media/donate-on-patreon.svg
[img-stars]: https://cdn.rawgit.com/ihodev/a-file-icon/dev/media/star-on-github.svg
[img-twitter]: https://cdn.rawgit.com/ihodev/a-file-icon/dev/media/share-on-twitter.svg
