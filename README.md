# dahu-2

## Contributing

### Common mistakes

#### Forms

If field or sub-form validation doesn't work, check if the field/sub-form calls
`super()\_\_init\_\_`.

#### Switch page

Don't use `st.switch_page` to go from current page P1 to another page P2 if 
P1 has query parameters in its URL. The browser's back button
will not restore these parameters if the user wants to go back. This will
break navigation.

In this case, use st.page_link, which will open the page
in a new tab. That way, if the user wants to go back, they will simply close
the newly opened tab. Not ideal but there is no satisfying alternative.

The `switch_button` function handles this automatically by detecting current
query parameters.